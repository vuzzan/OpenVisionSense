from flask import Flask, g, session, jsonify, send_from_directory, render_template, request, redirect, url_for
import os, shutil
import logging
from werkzeug.utils import secure_filename
from db import query_db, init_db
from flask_apscheduler import APScheduler

import job

app = Flask(__name__,
            static_folder='./static',
            template_folder='./templates')

app.secret_key = 'neoapp123'  # Needed for flash messages


scheduler = APScheduler()

if not os.path.exists("./logs"):
    os.makedirs("./logs")

# Configure logger for module1
logger_web = logging.getLogger(__name__)
logger_web.setLevel(logging.DEBUG)
fh1 = logging.FileHandler('logs/web.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh1.setFormatter(formatter)
logger_web.addHandler(fh1)
logger_web.addHandler(logging.StreamHandler())


@app.before_request
def set_global_variables():
    g.app_name = "Open VisionSense"
    g.app_version = "1.0"
    g.data_dir = app.root_path + "/data"


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', session=session)
    return render_template('login.html')


@app.route('/adminlte3/<path:filename>')
def base_static(filename):
    return send_from_directory(app.root_path + '/adminlte3/', filename)


@app.route('/data/<path:filename>')
def base_static_data_image(filename):
    return send_from_directory(app.root_path + '/data/', filename)



@app.route('/', methods=['GET'])
def home_action():
    if 'username' not in session:
        return render_template('login.html')
    # Next
    return redirect("/projects", 302)


@app.route('/logout', methods=['GET'])
def logout_action():
    del session['username']
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login_action():
    username = request.form['email']
    password = request.form['password']

    user = query_db("SELECT * FROM users WHERE username = ? AND password = ?",
              (username, password))
    # logger.info(user)
    if user:
        session['username'] = username  # Lưu username vào session
        data = {'status': 'ok', 'reason': 'ok'}
        return jsonify(data), 200
    else:
        data = {'status': 'false', 'reason': 'Can not found [' + username + "]"}
        return jsonify(data), 200


@app.route('/projects', methods=['POST', 'GET'])
def projects():
    if 'username' not in session:
        return render_template('login.html')
    # Next
    action = request.args.get('a')
    if action == None or action == "":
        return render_template('index.html', session=session)

    if action == "listobj":
        sql = "SELECT * FROM projects"
        list_obj = query_db(sql)
        for e in list_obj:
            classes = query_db("select class_id, class_name from project_classes where project_id="+str(e["project_id"]))
            for cls in classes:
                # project_dir = g.data_dir + "/project_"+str(obj)
                class_dir = g.data_dir + "/project_"+str(e["project_id"]) + "/class_" +str(cls["class_id"])
                cls["file_count"] = 0
                if os.path.exists("./data"):
                    _, _, files = next(os.walk(class_dir))
                    cls["file_count"] = len(files)
                else:
                    os.makedirs(class_dir)

            e["classes"] = classes
            logger_web.info(e)
        data = {"data": list_obj,
                "draw": request.form["draw"],
                "recordsFiltered": len(list_obj),
                "recordsTotal": len(list_obj),
                "sql": sql
                }
        return jsonify(data), 200
    elif action == "edit":
        sql = "SELECT * FROM projects where project_id=?"
        obj = query_db(sql, (request.args.get('id'), ), True)
        obj["classes"] = query_db("SELECT class_id, class_name FROM project_classes where project_id=?",
                                  (request.args.get('id'), ))
        return jsonify(obj), 200
    elif action == "edit_class":
        sql = "SELECT * FROM project_classes where class_id=?"
        obj = query_db(sql, (request.args.get('id'), ), True)
        return jsonify(obj), 200
    elif action == "update":
        sql = "update projects set project_name=? where project_id=?"
        obj = query_db(sql, (request.form["project_name"], request.form["id"]), True)
        return jsonify({"status": True}), 200
    elif action == "update_class":
        sql = "update project_classes set class_name=? where class_id=?"
        obj = query_db(sql, (request.form["class_name"], request.form["id"]), True)
        return jsonify({"status": True}), 200
    elif action == "add":
        # sql INSERT NEW PROJECT
        sql = "insert into projects(project_name) values ('"+request.form["project_name"]+"')"
        obj = query_db(sql)
        logger_web.info(obj)
        # CREATE NEW FOLDER FOR PROJECT
        project_dir = g.data_dir + "/project_"+str(obj)
        logger_web.info(project_dir)
        # MAKE DIRECTORY
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        return jsonify({"status": True, "id": obj}), 200
    elif action == "add_class":
        sql = "SELECT * FROM projects where project_id="+str(request.form["project_id"])
        project = query_db(sql, (), True)
        # sql INSERT NEW CLASS to PROJECT
        sql = "insert into project_classes(project_id,class_name,project_name) values (?,?,?)"
        class_id = query_db(sql, (request.form["project_id"], request.form["class_name"], project["project_name"]))
        logger_web.info("New class id=" + str(class_id))
        # CREATE NEW FOLDER FOR class_dir
        class_dir = g.data_dir + "/project_"+str(request.form["project_id"]) + "/class_" + str(class_id)
        logger_web.info(class_dir)
        # MAKE DIRECTORY
        if not os.path.exists(class_dir):
            os.makedirs(class_dir)
        return jsonify({"status": True, "id": class_id}), 200
    elif action == "delete_class_images":
        sql = "SELECT * FROM project_classes where class_id="+str(request.args.get('id'))
        class_obj = query_db(sql, (), True)
        logger_web.info("delete_class_images")
        class_dir = g.data_dir + "/project_" + str(class_obj["project_id"]) + "/class_" + str(class_obj["class_id"])
        logger_web.info("delete_class_images file " + class_dir)
        for filename in os.listdir(class_dir):
            file_path = os.path.join(class_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger_web.info('Failed to delete ' + file_path + '. Reason: ' + e)
    elif action == "delete_class":
        sql = "SELECT * FROM project_classes where class_id="+str(request.args.get('id'))
        class_obj = query_db(sql, (), True)
        logger_web.info("delete_class_images")
        class_dir = g.data_dir + "/project_" + str(class_obj["project_id"]) + "/class_" + str(class_obj["class_id"])
        logger_web.info("delete_class_images file " + class_dir)
        for filename in os.listdir(class_dir):
            file_path = os.path.join(class_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger_web.info('Failed to delete ' + file_path + '. Reason: ' + e)
        shutil.rmtree(class_dir)
        # Delete class
        sql = "delete from project_classes where class_id=?"
        query_db(sql, (request.args.get('id'),), True)
        return jsonify(class_obj), 200
        # END
    elif action == "start_train":
        sql = "SELECT * FROM project_classes where project_id="+str(request.args.get('id'))
        class_list = query_db(sql, (), False)
        logger_web.info("start_train")
        project_dir = g.data_dir + "/project_" + request.args.get('id')
        # check valid
        check_valid_msg = ""
        for class_obj in class_list:
            class_dir = project_dir + "/class_" + str(class_obj["class_id"])
            _, _, files = next(os.walk(class_dir))
            total_file = len(files)
            if total_file<0:
                check_valid_msg += "-"+class_obj["class_name"] + " images < 200. Cannot train.."
        if len(check_valid_msg)==0:
            # OK
            sql = "update projects set project_status='QueueTraining' where project_id=" + str(request.args.get('id'))
            query_db(sql, (), False)
            return jsonify({"status": True, "msg": "Start train..."}), 200
        else:
            return jsonify({"status": False, "msg": check_valid_msg}), 200
    elif action == "delete":
        sql = "SELECT * FROM project_classes where project_id="+str(request.args.get('id'))
        class_list = query_db(sql, (), False)
        logger_web.info("delete_project")
        project_dir = g.data_dir + "/project_" + request.args.get('id')
        for class_obj in class_list:
            class_dir = project_dir + "/class_" + str(class_obj["class_id"])
            logger_web.info("delete_project file " + project_dir)
            for filename in os.listdir(class_dir):
                file_path = os.path.join(class_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger_web.info('Failed to delete ' + file_path + '. Reason: ' + e)
            shutil.rmtree(class_dir)
        if os.path.isdir(project_dir):
            shutil.rmtree(project_dir)
        # Delete class
        sql = "delete from project_classes where project_id="+str(request.args.get('id'))
        query_db(sql, (), True)
        sql = "delete from projects where project_id="+str(request.args.get('id'))
        query_db(sql, (), True)
        return jsonify(request.args.get('id')), 200
        # END
    elif action == "upload_file":
        sql = "SELECT * FROM project_classes where class_id="+str(request.form["id"])
        class_obj = query_db(sql, (), True)
        logger_web.info("upload_file")
        logger_web.info(class_obj)
        # upload file - save file
        if request.method == 'POST':
            # check if the post request has the file part
            logger_web.info("Save file ")
            if 'file' not in request.files:
                return jsonify({"result": False, "msg": "No files"}), 200
            file = request.files['file']
            logger_web.info(file)
            logger_web.info("Save file 2")
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            class_dir = g.data_dir + "/project_" + str(class_obj["project_id"]) + "/class_" + str(class_obj["class_id"])
            logger_web.info("Save file " + class_dir)
            _, _, files = next(os.walk(class_dir))
            file_count = len(files) + 1
            if file.filename == '':
                return jsonify({"result": False, "msg": 'No selected file'}), 200
            file_extension = os.path.splitext(file.filename)[1]
            if file and allowed_file(file.filename):
                #filename = secure_filename(file.filename)
                file.save(os.path.join(class_dir, str(file_count) + file_extension))
                class_obj["file_path"] = class_dir + "/" + str(file_count) + file_extension;
        return jsonify(class_obj), 200
    elif action == "upload_file_run_model":
        sql = "SELECT * FROM projects where project_id=?"
        obj = query_db(sql, (request.form["id"], ), True)
        logger_web.info("upload_file_run_model")
        # get file image
        if 'file' not in request.files:
            return jsonify({"result": False, "msg": "No files"}), 200
        file = request.files['file']
        project_dir = "/project_" + str(obj["project_id"]) + "/queue"
        tmp_dir = g.data_dir + project_dir
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        logger_web.info("Save file " + tmp_dir)
        if file.filename == '':
            return jsonify({"result": False, "msg": 'No selected file'}), 200
        file_extension = os.path.splitext(file.filename)[1]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(tmp_dir, filename))
            obj["file_path"] = tmp_dir + "/" + filename
            sql = "insert into queue_jobs(project_id,project_name,source_file_path) values(?,?,?)"
            job_id = query_db(sql, (request.form["id"], str(obj["project_name"]), os.path.join(project_dir, filename)))
            obj["job_id"] = job_id
            logger_web.info("add upload_file_run_model")
        return jsonify(obj), 200
    return jsonify(()), 200


@app.route('/jobs', methods=['POST', 'GET'])
def job_action():
    if 'username' not in session:
        return render_template('login.html')
    # Next
    action = request.args.get('a')
    if action==None or action == "":
        return render_template('jobs.html', session=session)

    if action == "listobj":
        sql = "SELECT * FROM queue_jobs order by job_id desc"
        list_obj = query_db(sql)
        data = {"data": list_obj,
                "draw": request.form["draw"],
                "recordsFiltered": len(list_obj),
                "recordsTotal": len(list_obj),
                "sql": sql
                }
        return jsonify(data), 200
    elif action == "edit":
        sql = "SELECT * FROM projects where project_id=?"
        obj = query_db(sql, (request.args.get('id'), ), True)
        obj["classes"] = query_db("SELECT class_id, class_name FROM project_classes where project_id=?",
                                  (request.args.get('id'), ))
        return jsonify(obj), 200

    return jsonify(()), 200


if __name__ == '__main__':
    init_db()  # Initialize database when app starts
    scheduler.add_job(id='Scheduled Task Training',
                      func=job.schedule_task_training,
                      trigger="interval",
                      seconds=3,
                      )
    scheduler.add_job(id='Scheduled Task start_job_run_model',
                      func=job.schedule_task_run_model,
                      trigger="interval",
                      seconds=3,
                      )
    scheduler.start()
    app.run(debug=True, host="0.0.0.0", port=5000)
