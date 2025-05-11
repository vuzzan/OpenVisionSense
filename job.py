from db import query_db
import os,shutil
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/jobs.log', level=logging.DEBUG)


def start_job(job):
    logger.info("start_job ")
    logger.info(job)
    sql = "update projects set project_status='StartTraining' where project_id=" + str(job["project_id"])
    query_db(sql, (), False)


def schedule_task():
    #print("schedule_task This test runs every 3 seconds")
    sql = "select * from projects where project_status='QueueTraining'"
    job_list = query_db(sql, ())
    if len(job_list)==0:
        print("No job QueueTraining...")
    for job in job_list:
        job["classes"] = query_db("select * from project_classes where project_id=" + str(job["project_id"]), ())
        start_job(job)