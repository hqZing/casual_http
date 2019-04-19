from flask import *
import flask
import hashlib


app = flask.Flask(__name__)

f = open('README.md', 'rb')


@app.route('/image/<file_id>')
def images(file_id):
    file = f
    rv = send_file(file,
        mimetype=file.content_type,
        # as_attachment=True,
        attachment_filename=file.filename,
        add_etags=False,
        conditional=True
    )

    rv.last_modified = file.upload_date
    # app.logger.debug(rv.last_modified)    # 2012-11-24 08:51:27
    # app.logger.debug(request.if_modified_since)    # 2012-11-24 08:51:27
    # app.logger.debug(rv.last_modified<=request.if_modified_since)    # True
    print(rv.last_modified)
    print(request.if_modified_since)
    print(rv.last_modified<=request.if_modified_since)
    rv.make_conditional(request)
    return rv

app.run()

