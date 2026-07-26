import csv
import io
from flask import Blueprint, request, g, Response
from database.db import get_db
from utils.response import success, fail
from utils.auth import login_required

import_bp = Blueprint('import', __name__)

@import_bp.route('/csv/<int:category_id>', methods=['POST'])
@login_required
def import_csv(category_id):
    """导入CSV数据到指定管理项"""
    if 'file' not in request.files:
        return fail('请上传CSV文件')

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return fail('仅支持CSV文件')

    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    fields = conn.execute(
        "SELECT * FROM category_fields WHERE category_id = ? ORDER BY sort_order",
        (category_id,)
    ).fetchall()

    table_name = cat['table_name']
    field_keys = [f['field_key'] for f in fields]
    field_labels = [f['field_label'] for f in fields]

    try:
        # 自动检测编码：依次尝试 utf-8-sig → gb18030 → gbk → gb2312
        raw = file.read()
        content = None
        for enc in ['utf-8-sig', 'gb18030', 'gbk', 'gb2312']:
            try:
                content = raw.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if content is None:
            conn.close()
            return fail('无法识别CSV文件编码，请将文件另存为UTF-8编码')
        reader = csv.DictReader(io.StringIO(content))

        if not reader.fieldnames:
            conn.close()
            return fail('CSV文件为空或格式不正确')

        # 建立CSV列名到字段key的映射（按标签匹配或按顺序匹配）
        csv_headers = [h.strip() for h in reader.fieldnames]
        mapping = {}
        for i, label in enumerate(field_labels):
            if label in csv_headers:
                mapping[label] = field_keys[i]
            elif i < len(csv_headers):
                # 按顺序映射
                mapping[csv_headers[i]] = field_keys[i]

        if not mapping:
            conn.close()
            return fail('无法匹配CSV列与数据库字段')

        imported = 0
        errors = []
        for row_num, row in enumerate(reader, start=2):
            try:
                values = {}
                for csv_col, db_col in mapping.items():
                    values[db_col] = row.get(csv_col, '')

                cols = ', '.join(values.keys())
                placeholders = ', '.join(['?'] * len(values))
                sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
                conn.execute(sql, list(values.values()))
                imported += 1
            except Exception as e:
                errors.append(f'第{row_num}行: {str(e)}')

        conn.commit()
        conn.close()
        return success({'imported': imported, 'errors': errors}, f'成功导入 {imported} 条记录')
    except Exception as e:
        conn.close()
        return fail(f'导入失败: {str(e)}')

@import_bp.route('/csv/<int:category_id>', methods=['GET'])
@login_required
def export_csv(category_id):
    """导出指定管理项的数据为CSV"""
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    fields = conn.execute(
        "SELECT * FROM category_fields WHERE category_id = ? ORDER BY sort_order",
        (category_id,)
    ).fetchall()

    table_name = cat['table_name']
    field_keys = [f['field_key'] for f in fields]
    field_labels = [f['field_label'] for f in fields]

    rows = conn.execute(f"SELECT {', '.join(field_keys)} FROM {table_name} ORDER BY id").fetchall()
    conn.close()

    output = io.StringIO()
    # UTF-8 BOM for Excel compatibility with Chinese characters
    output.write('\ufeff')
    writer = csv.writer(output)

    # 表头：中文标签
    writer.writerow(field_labels)

    # 数据行
    for row in rows:
        writer.writerow([row[fk] for fk in field_keys])

    csv_content = output.getvalue()
    output.close()

    filename = f"{cat['name']}.csv"
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename.encode("utf-8").decode("latin-1")}"',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )
