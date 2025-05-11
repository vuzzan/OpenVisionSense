from flask import Flask, g, session, jsonify, send_from_directory, render_template, request, redirect, url_for
import os, shutil
import logging
from werkzeug.utils import secure_filename
from db import query_db, init_db

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/web.log', level=logging.DEBUG)