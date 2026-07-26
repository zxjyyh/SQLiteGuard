from flask import jsonify

def success(data=None, message='ok'):
    return jsonify({'code': 0, 'message': message, 'data': data})

def fail(message='error', code=-1):
    return jsonify({'code': code, 'message': message, 'data': None})

def paginated(data_list, total, page, page_size):
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'list': data_list,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    })
