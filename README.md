# aristotle
    git clone git@github.com:yonigottesman/aristotle.git
    cd aristotle
    python3 -m venv venv
    source venv/bin/activate
    pip3 install -r requirements.txt

    flask db upgrade

    export FLASK_APP=aristotle.py
    export FLASK_DEBUG=1
    flask run
