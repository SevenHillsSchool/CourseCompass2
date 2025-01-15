from flask import Flask, redirect, url_for, request, render_template
import mysql.connector

app = Flask(__name__)

# Creates a connection to the database
def connectToData():
    dataBase = mysql.connector.connect(
        host="sql5.freemysqlhosting.net",
        user="sql5744928",
        passwd="wCBdQqsKCG",
        database="sql5744928"
    )
    return dataBase

@app.route('/')
def pythonHome():
    return render_template("Home.html")

@app.route('/navBar')
def navBar():
    return render_template("NavigationBar.html")

def populate():
    # Connecting to the server
    dataBase = connectToData()

    # preparing a cursor object
    cursor = dataBase.cursor()
    statement = "SELECT divisionName FROM division"
    cursor.execute(statement)
    divisions = []
    for x in cursor.fetchall():
        divisions.append(x[0].replace("'", ""))

    statement = "SELECT subjectName FROM subject"
    cursor.execute(statement)
    subjects = []
    for x in cursor.fetchall():
        subjects.append(x[0].replace("'", ""))

    statement = "SELECT courseName FROM CourseInfo"
    cursor.execute(statement)
    courses = []
    for x in cursor.fetchall():
        courses.append(x[0].replace("'", ""))

    statement = "SELECT teacherName FROM teacherName"
    cursor.execute(statement)
    teachers = []
    for x in cursor.fetchall():
        currTeacherList = x[0].replace("'", "").split(", ")
        if len(currTeacherList) >= 2:
            currTeacher = currTeacherList[1] + " " + currTeacherList[0]
        else:
            currTeacher = currTeacherList[0]
        teachers.append(currTeacher)

    return {
        'Divisions':str(divisions).removeprefix("[").removesuffix("]"), 
        'Subjects':str(subjects).removeprefix("[").removesuffix("]"),
        'Courses':str(courses).removeprefix("[").removesuffix("]"),
        'Teachers':str(teachers).removeprefix("[").removesuffix("]")
    }

@app.route('/browse')
def browse():
    dropDownData = populate()
    print(dropDownData)
    return render_template("browse.html", dropDownData=dropDownData, searchData = "")

# Used to search the database with inputs from the browse page
@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        data = request.form['data'].replace("\"", "").split(",")
        # Process the received data
        # School, Department, Course, teacher
        school = data[0]
        department = data[1]
        course = data[2]
        teacher = data[3]
        dataBase = connectToData()
        results = []
        noResults = False
        #try:
        # preparing a cursor object
        cursor = dataBase.cursor()
        # Prepares the initial sql query
        statement = "SELECT * FROM CourseInfo"
        original = statement

        # Getting the school id from the division table based on the division name
        if school != "":
            statementSchool = "SELECT divisionID FROM division WHERE divisionName='" + school + "'"
            cursor.execute(statementSchool)
            schoolId = cursor.fetchall()[0][0]
            if statement == original:
                statement+=" WHERE "
            if "=" in statement:
                statement += " AND "
            statement+="divisionID='" + str(schoolId) + "'"

        # Getting the subject id from the Subjects table
        if department != "":
            statementDepartment = "SELECT subjectId FROM subject WHERE subjectName='" + department + "'"
            cursor.execute(statementDepartment)
            subjectId = cursor.fetchall()[0][0]
            if statement == original:
                statement+=" WHERE "
            if "=" in statement:
                statement += " AND "
            statement+= "subjectID='" + str(subjectId) + "'"

        # Getting the courses from the course info table based on the course name
        if course != "":
            if statement == original:
                statement+=" WHERE "
            if "=" in statement:
                statement += " AND "
            statement+="courseName='" + str(course) + "'"

        # Getting the teacher id from the teacherName table based on the teacher name
        teacherCourses = []
        currTeacher = teacher.split(" ")
        if len(currTeacher) > 1:
            teacher = currTeacher[1] + ", " + currTeacher[0]
        else:
            teacher = currTeacher[0]
        if teacher != "":
            statementTeacher = "SELECT userID FROM teacherName WHERE teacherName='" + teacher + "'"
            cursor.execute(statementTeacher)
            teacherId = cursor.fetchall()[0][0]
            cursor.execute("SELECT courseID FROM courseTeacher WHERE userID='%i'" % teacherId)
            if len(cursor.fetchall()) != 0:
                statementTeacher = "SELECT courseID FROM courseTeacher WHERE userID='" + str(teacherId) + "'"
                cursor.execute(statementTeacher)
                for i in cursor.fetchall():
                    teacherCourses.append(str(i[0]))

                if statement == original:
                    statement+=" WHERE "
                if "=" in statement:
                    statement += " AND "
                statement+="courseID IN ("
                for i in teacherCourses:
                    statement+= i+", "
                statement = statement[:-2]
                statement+=")"
            else:
                noResults = True
            
        if not noResults:
            cursor.execute(statement)
            results = cursor.fetchall()

        # except:
        #     print("Error Getting Results")

        # Formatting the course name and course ids into a string
        strNames = ""
        strIds = ""
        for i in results:
            strNames += i[1]+","
            strIds += str(i[0]) + ","
        strNames = strNames[0:len(strNames)-1]
        strIds = strIds[0:len(strIds)-1]
        if strNames == "":
            strNames = "No Results"

        searchData = {
            'Names':strNames,
            'Ids':strIds
        }
        return searchData

# Used to get all the details about a class
@app.route("/getCourseInfo", methods=['POST'])
def getCourseInfo():
    courseId = int(request.form['data'])
    dataBase = connectToData()
    cursor = dataBase.cursor()
    cursor.execute("SELECT courseName FROM CourseInfo WHERE courseID='%i'" % courseId)
    courseTitle = cursor.fetchall()[0][0]
    cursor.execute("SELECT userID FROM courseTeacher WHERE courseID='%i'" % courseId)
    userId = cursor.fetchall()[0][0]
    cursor.execute("SELECT teacherName FROM teacherName WHERE userID='%i'" % int(userId))
    teacherName = cursor.fetchall()[0][0]
    cursor.exeucte("SELECT unitID, unitName FROM Unit WHERE courseID='%i'" % courseId)
    unitInfo = cursor.fetchall()
    unitIds = [unit[0] for unit in unitInfo]
    unitNames = [unit[1] for unit in unitInfo]

    courseInfo =  {
        "Title":courseTitle,
        "Teacher":teacherName,
        "UnitIds":str(unitIds).removeprefix("[").removesuffix("]"),
        "UnitNames":str(unitNames).removeprefix("[").removesuffix("]")
    } 
    return render_template("courseInfo.html", courseInfo=courseInfo)

# Used to get all the details about a class
@app.route("/getUnitInfo", methods=['POST'])
def getInfo():
    unitId = int(request.form['data'])
    '''
    Title
    Duration - Doesn't exist yet?
    Standards
    Objectives
    Essential Questions
    Unit Description
    '''
    # Getting all of the data about the unit
    dataBase = connectToData()
    cursor = dataBase.cursor()
    cursor.execute("SELECT unitName FROM Unit WHERE unitID=%i" % unitId)
    unitTitle = cursor.fetchall()[0][0]
    cursor.execute("SELECT * FROM unitText WHERE unitID=%i" % unitId)
    rawUnitData = cursor.fetchall()  
    # RawUnitData is all the data from unitText which is everything but title
    # This will be in a 2d array (theCategoryId, theText)
    # Somehow we have to put this in my allData dict so that the category type in english matches to the text from the 2d array
    # The array is not ordered by categoryId

    allData = {
        "Title":unitTitle, 
        # "Standards": Array to Dict?
    }
    return render_template("LessonPlanPage.html", allData=allData)

# Used for the edit course page to edit the courses
@app.route("/editCourse") #, methods=['POST'])
def editCourse():
    return "Nothing here yet"

# Used for adding a course
@app.route("/addCourse")
def addCourse():
    # textFields = request.form['data'].split(",")
    # name = textFields[0]
    # year = textFields[1]
    # grades = textFields[2]
    # subject = textFields[3]
    # division = textFields[4]
    # teacher = textFields[5]
    # units = textFields[6].split(",")
    name = "Computer Science 3"
    year = "2024"
    grades = "grades 10-12"
    subject = "English"
    division = "Upper"
    teacher = "Marcus Twyford"
    units = ["1:Text", "2:Text", "3:Text"]

    # Connecting to the server
    dataBase = connectToData()

    # preparing a cursor object
    cursor = dataBase.cursor()
    # Add a new subject if the subject does not exist
    cursor.execute("SELECT subjectID FROM subject WHERE subjectName='%s'" % subject)
    if len(cursor.fetchall()) == 0:
        cursor.execute("INSERT INTO subject (subjectName) VALUES ('%s')" % subject)
    
    # Add a new division if that division does not exist
    cursor.execute("SELECT divisionID FROM division WHERE divisionName='%s'" % division)
    if len(cursor.fetchall()) == 0:
        cursor.execute("INSERT INTO subject VALUES ('%s')" % division)

    cursor.execute("SELECT subjectID FROM subject WHERE subjectName='%s'" % subject)
    subId = int(cursor.fetchone()[0])
    cursor.fetchall()
    cursor.execute("SELECT divisionID FROM division WHERE divisionName='%s'" % division)
    divId = int(cursor.fetchone()[0])
    cursor.fetchall()

    # Add to the courseInfo table
    statement = "INSERT INTO CourseInfo (courseName, subjectID, year, grade, divisionID) VALUES ('%s', %i, %i, '%s', %i)" % (name, subId, int(year), grades, divId)
    cursor.execute(statement)

    cursor.execute("SELECT @@IDENTITY")
    courseId = int(cursor.fetchall()[0][0])

    # Add to the teacher table
    cursor.execute("SELECT userID FROM teacherName WHERE teacherName='%s'" % teacher)
    if len(cursor.fetchall()) == 0:
        statement = "INSERT INTO teacherName VALUES ('%s')" % (teacher)
        cursor.execute(statement)
        cursor.execute("SELECT SCOPE_IDENTITY()")
        teacherId = cursor.fetchall()[0]
    else:
        cursor.execute("SELECT userID FROM teacherName WHERE teacherName='%s'" % teacher)
        teacherId = int(cursor.fetchall()[0][0])
    # Add to the courseTeacher table
    statement = "INSERT INTO courseTeacher VALUES (%i, %i)" % (courseId, teacherId)
    cursor.execute(statement)

    # Adding the units to the unit table
    for unit in units:
        unitName = unit.split(":")[0]
        unitText = unit.split(":")[1]
        cursor.execute("INSERT INTO Unit (unitName, courseID) VALUES (%s, %i)" % (unitName, courseId))
        cursor.execute("")

    #dataBase.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
