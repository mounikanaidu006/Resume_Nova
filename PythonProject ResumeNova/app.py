import json
import os
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.utils import secure_filename

from analyzer import analyze_resume


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "resumenova-local-secret-key"


# =========================================================
# FOLDERS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

RESULT_FOLDER = os.path.join(
    BASE_DIR,
    "analysis_results"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    8 * 1024 * 1024
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    RESULT_FOLDER,
    exist_ok=True
)


# =========================================================
# PDF VALIDATION
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower() == "pdf"
    )


# =========================================================
# RESULT FILE HELPERS
# =========================================================

def get_result_path(analysis_id):

    return os.path.join(
        RESULT_FOLDER,
        f"{analysis_id}.json"
    )


def save_analysis_result(
    analysis_id,
    result
):

    path = get_result_path(
        analysis_id
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2
        )


def load_analysis_result(
    analysis_id
):

    if not analysis_id:
        return None

    path = get_result_path(
        analysis_id
    )

    if not os.path.exists(path):
        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (
        OSError,
        json.JSONDecodeError
    ):

        return None


def delete_analysis_result(
    analysis_id
):

    if not analysis_id:
        return

    path = get_result_path(
        analysis_id
    )

    if os.path.exists(path):

        try:
            os.remove(path)

        except OSError:
            pass


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return redirect(
        url_for("login")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=[
        "GET",
        "POST"
    ]
)
def login():

    error = None

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        if len(name) < 2:

            error = (
                "Please enter your name."
            )


        elif len(password) < 4:

            error = (
                "Password must contain "
                "at least 4 characters."
            )


        else:

            # Remove previous result
            old_analysis_id = (
                session.get(
                    "analysis_id"
                )
            )

            delete_analysis_result(
                old_analysis_id
            )

            # Clear old user's session
            session.clear()

            # New user session
            session["user_name"] = name

            return redirect(
                url_for("upload")
            )


    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    analysis_id = session.get(
        "analysis_id"
    )

    delete_analysis_result(
        analysis_id
    )

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# UPLOAD PAGE
# =========================================================

@app.route("/upload")
def upload():

    if "user_name" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "upload.html",
        user_name=session[
            "user_name"
        ]
    )


# =========================================================
# ANALYZE RESUME
# =========================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    if "user_name" not in session:

        return redirect(
            url_for("login")
        )


    # -----------------------------------------------------
    # FORM INPUTS
    # -----------------------------------------------------

    resume = request.files.get(
        "resume"
    )

    job_role = request.form.get(
        "job_role",
        ""
    ).strip()

    job_description = request.form.get(
        "job_description",
        ""
    ).strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if (
        resume is None
        or
        resume.filename == ""
    ):

        return render_template(
            "upload.html",
            user_name=session[
                "user_name"
            ],
            error=(
                "Resume PDF is required."
            )
        )


    if not job_role:

        return render_template(
            "upload.html",
            user_name=session[
                "user_name"
            ],
            error=(
                "Target Job Role is required."
            )
        )


    if not job_description:

        return render_template(
            "upload.html",
            user_name=session[
                "user_name"
            ],
            error=(
                "Job Description is required."
            )
        )


    if len(job_description) < 30:

        return render_template(
            "upload.html",
            user_name=session[
                "user_name"
            ],
            error=(
                "Please enter a more complete "
                "Job Description."
            )
        )


    if not allowed_file(
        resume.filename
    ):

        return render_template(
            "upload.html",
            user_name=session[
                "user_name"
            ],
            error=(
                "Please upload a PDF file."
            )
        )


    # -----------------------------------------------------
    # SAVE TEMPORARY PDF
    # -----------------------------------------------------

    original_filename = (
        secure_filename(
            resume.filename
        )
    )

    unique_filename = (
        f"{uuid.uuid4().hex}_"
        f"{original_filename}"
    )

    pdf_path = os.path.join(
        app.config[
            "UPLOAD_FOLDER"
        ],
        unique_filename
    )


    try:

        resume.save(
            pdf_path
        )


        # -------------------------------------------------
        # ACTUAL ANALYSIS
        # -------------------------------------------------

        result = analyze_resume(
            pdf_path,
            job_role,
            job_description
        )


        # -------------------------------------------------
        # ADD REPORT INFORMATION
        # -------------------------------------------------

        result["filename"] = (
            original_filename
        )

        result["job_role"] = (
            job_role
        )


        # -------------------------------------------------
        # DELETE PREVIOUS RESULT
        # -------------------------------------------------

        old_analysis_id = (
            session.get(
                "analysis_id"
            )
        )

        delete_analysis_result(
            old_analysis_id
        )


        # -------------------------------------------------
        # CREATE NEW RESULT ID
        # -------------------------------------------------

        analysis_id = (
            uuid.uuid4().hex
        )


        # -------------------------------------------------
        # SAVE RESULT SERVER-SIDE
        # -------------------------------------------------

        save_analysis_result(
            analysis_id,
            result
        )


        # Only small ID stored in session
        session["analysis_id"] = (
            analysis_id
        )


    except Exception as error:

        return render_template(
            "upload.html",
            user_name=session[
                "user_name"
            ],
            error=(
                "Resume analysis failed: "
                f"{str(error)}"
            )
        )


    finally:

        # Temporary uploaded PDF is removed
        if os.path.exists(
            pdf_path
        ):

            try:
                os.remove(
                    pdf_path
                )

            except OSError:
                pass


    # -----------------------------------------------------
    # ANALYZING SCREEN
    # -----------------------------------------------------

    return render_template(
        "analyzing.html"
    )


# =========================================================
# RESULT PAGE
# =========================================================

@app.route("/result")
def result():

    if "user_name" not in session:

        return redirect(
            url_for("login")
        )


    analysis_id = session.get(
        "analysis_id"
    )


    if not analysis_id:

        return redirect(
            url_for("upload")
        )


    analysis_result = (
        load_analysis_result(
            analysis_id
        )
    )


    if analysis_result is None:

        session.pop(
            "analysis_id",
            None
        )

        return redirect(
            url_for("upload")
        )


    return render_template(
        "result.html",
        result=analysis_result,
        user_name=session[
            "user_name"
        ]
    )


# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def too_large(error):

    if "user_name" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "upload.html",
        user_name=session[
            "user_name"
        ],
        error=(
            "PDF is too large. "
            "Maximum allowed size is 8 MB."
        )
    ), 413


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )