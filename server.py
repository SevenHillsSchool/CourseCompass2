from flask import Flask, redirect, url_for, request, render_template
import mysql.connector
import json
from urllib.parse import unquote

app = Flask(__name__)

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

@app.route('/courseInfo')
def courseInfo():
    return render_template("CourseInformationPage.html")

@app.route('/editPage', methods=['POST'])
def editPage():
    # Get the encoded JSON string from the form data
    encoded_unit_data = request.form.get('unitData')
    
    # Decode the URL-encoded string
    decoded_unit_data = unquote(encoded_unit_data)
    print("Data: " + decoded_unit_data)
    return render_template("LessonPlanPage.html", unitData=decoded_unit_data)

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

    statement = "SELECT teacherName FROM teacherName"
    cursor.execute(statement)
    teachers = []
    teachersRaw = []
    for x in cursor.fetchall():
        teachersRaw.append(x[0].replace("'", ""))
    teachersRaw.sort()
    for teacher in teachersRaw:
        currTeacherList = teacher.split(", ")
        if len(currTeacherList) >= 2:
            currTeacher = (currTeacherList[1] + " " + currTeacherList[0]).title()
        else:
            currTeacher = currTeacherList[0]
        teachers.append(currTeacher)
    divisions.sort()
    subjects.sort()
    teachers
    dataToReturn = {
        'Divisions':str(divisions).removeprefix("[").removesuffix("]"), 
        'Subjects':str(subjects).removeprefix("[").removesuffix("]"),
        'Teachers':str(teachers).removeprefix("[").removesuffix("]")
    }

    return dataToReturn

@app.route('/browse')
def browse():
    dropDownData = populate()
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
        teacher = data[2]
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
        rawNamesIds = {}
        for i in results:
            rawNamesIds[str(i[0])] = i[1]
        namesIdsSorted = sorted(rawNamesIds.items(), key=lambda kv: (kv[1], kv[0]))
        for entry in namesIdsSorted:
            strNames += entry[1]+","
            strIds += entry[0]+","
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
    teacherName = "No Teacher"
    courseId = int(request.form['data'])
    dataBase = connectToData()
    cursor = dataBase.cursor()
    global categoryKey
    categoryKey = dict()
    cursor.execute("SELECT * FROM categoryType")
    categories = cursor.fetchall()
    for category in categories:
        categoryKey[category[0]] = category[1]
    cursor.execute("SELECT courseName FROM CourseInfo WHERE courseID='%i'" % courseId)
    courseTitle = cursor.fetchall()[0][0]
    teachers = []
    cursor.execute("SELECT userID FROM courseTeacher WHERE courseID='%i'" % courseId)
    userId = cursor.fetchall()
    # Get a list of user IDs from userId
    user_ids = [int(user[0]) for user in userId]
    teachers = []

    if user_ids:
        # Create a parameterized IN-clause
        format_strings = ','.join(['%s'] * len(user_ids))
        query = "SELECT teacherName FROM teacherName WHERE userID IN ({})".format(format_strings)
        cursor.execute(query, tuple(user_ids))
        teacherRows = cursor.fetchall()

        # Process each teacherName from the batch query result
        for row in teacherRows:
            teacherName = row[0]
            parts = teacherName.split(", ")
            if len(parts) >= 2:
                formatted = (parts[1] + " " + parts[0]).title()
                teachers.append(formatted)
            else:
                teachers.append(teacherName)
    cursor.execute("SELECT unitID, unitName FROM Unit WHERE courseID='%i'" % courseId)
    unitInfo = cursor.fetchall()
    unitIds = [unit[0] for unit in unitInfo]
    unitNames = [unit[1] for unit in unitInfo]

    teacherStr = ""
    for teacher in teachers:
        teacherStr += (teacher.replace("'", "") + ", ")
    

    courseInfo =  {
        "Title":courseTitle,
        "Teacher":teacherStr.removesuffix(", "),
        "UnitIds":str(unitIds).removeprefix("[").removesuffix("]"),
        "UnitNames":str(unitNames).removeprefix("[").removesuffix("]")
    } 
    unitInfo = {}
    for unit in unitIds:
        unitInfo["Id" + str(unit)] = getUnitInfo(unit)
    return render_template("CourseInformationPage.html", courseInfo=courseInfo, unitInfo=unitInfo)

# Used to get all the details about a class
def getUnitInfo(unitId):
    # Getting all of the data about the unit in a single query
    dataBase = connectToData()
    cursor = dataBase.cursor()
    allData = {}

    # Retrieve all unitText rows for the given unitId in one query
    query = "SELECT categoryTypeID, text FROM unitText WHERE unitID = %s"
    cursor.execute(query, (unitId,))
    rows = cursor.fetchall()

    # Map each row's category to its text using categoryKey
    for categoryID, text in rows:
        if categoryID in categoryKey:
            allData[categoryKey[categoryID]] = text

    cursor.close()
    dataBase.close()
    return allData

@app.route("/saveEdits", methods=['POST'])
def saveEdits():
    """ TODO:
        Get category type ID from category name
            - This will require us to ensure category names passed into this method are identical to those in the database
        Update specific columns of unitText based on categoryType and categoryName
        ADD THE ABILITY TO CHANGE/SAVE TITLE (Make it a rich text box)
    
    """

    edits = request.form['editData'].split("@#|")
    categoryCopy = {value: key for key, value in categoryKey.items()}
    dataBase = connectToData()
    cursor = dataBase.cursor()
    print(categoryCopy)
    unitID = edits[0]
    print(unitID)
    for edit in edits[1:]:
        if edit:
            print(edit.split("||| "))
            contentType, content = edit.split("||| ")
            if contentType == "Title":
                pass
            else:
                currCategory = categoryCopy[contentType]
                print(currCategory)
                statement = "UPDATE unitText SET text = %s WHERE unitID = %s AND categoryTypeID = %s"
                cursor.execute(statement, (content, unitID, currCategory))
                print("Rows affected:", cursor.rowcount)

    
    dataBase.commit()
    return edits

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
    app.run(host='0.0.0.0', port=8000, debug=True)
