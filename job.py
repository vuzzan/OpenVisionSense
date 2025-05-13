import time

from db import query_db
import os,shutil
import logging

# Configure logger for module1
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh1 = logging.FileHandler('logs/jobs.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh1.setFormatter(formatter)
logger.addHandler(fh1)
logger.addHandler(logging.StreamHandler())
job_id = 0


def start_job_training(job):
    logger.info("start_job_training projects StartTraining")
    logger.info(job)
    sql = "update projects set project_status='StartTraining' where project_id=?"
    query_db(sql, (job["project_id"], ), False)
    # Do training --
    # traing Triet lam
    project_model = "project_model.file"
    project_status = "Training Done"        # Or training fail

    # Training done
    sql = "update projects set project_status=?,project_model=? where project_id=?"
    query_db(sql, (project_status, project_model, job["project_id"]), False)
    logger.info("start_job projects StartTraining")


def start_job_run_model(job):
    logger.info("start_job_run_model queue_jobs ")
    logger.info(job)
    sql = "update queue_jobs set job_status='Start Job' where job_id=?"
    query_db(sql, (job["job_id"], ), False)
    # process job here
    sql = "select * from projects where project_id=?"
    project = query_db(sql, (job["project_id"], ), False)
    # Process with model
    model_file = project["project_model"]
    source_file_path = job["source_file_path"]
    # do predict

    result_file_path = ""
    job_class = 14
    job_result = "80%, class14"  #string

    # End competed
    sql = "update queue_jobs set job_result=?, result_file_path=?, job_class=?, job_status='Done' where job_id=?"
    query_db(sql, (job_result, result_file_path, job_class, job["job_id"]), False)
    logger.info("start_job2 queue_jobs done")


def schedule_task_training():
    global job_id
    sql = "select * from projects where project_status='QueueTraining'"
    job_list = query_db(sql, ())
    if len(job_list)==0:
        # Unit test job running
        # job_id = job_id + 1
        my_id = job_id
        # logger.info("#" + str(my_id) + " Start QueueTraining...")
        # time.sleep(10)
        #logger.info("#" + str(my_id) + " Job QueueTraining...END ")

    for job in job_list:
        job["classes"] = query_db("select * from project_classes where project_id=" + str(job["project_id"]), ())
        start_job_training(job)


def schedule_task_run_model():
    global job_id

    # Job list
    sql = "select * from queue_jobs where job_status='Wait Run'"
    job_list2 = query_db(sql, ())
    for job2 in job_list2:
        start_job_run_model(job2)