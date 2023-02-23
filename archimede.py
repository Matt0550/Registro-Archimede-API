import requests
import re
from bs4 import BeautifulSoup
import mechanize
import http.cookiejar as cookielib 
import json

class RegistroArchimede:
    
    def __init__(self, username, password):
        self.session = requests.session()
        self.cookies = self.session.cookies
        self.username = username
        self.password = password
        self.cid = None
        self.controlli = None
        self.login(username, password)

    def login(self, username, password):
        print("Logging in...")
        # Login to the website with username and password and set cookies
        URL = "https://accesso.registroarchimede.it/archimede/login.seam"
        cj = cookielib.CookieJar()
        br = mechanize.Browser()
        br.addheaders = [('User-agent', 'Mozilla/5.0 ')]
        br.set_cookiejar(cj)
        br.open(URL)

        br.select_form(nr=0)
        br.form['loginForm:username'] = username
        br.form['loginForm:password'] = password
        br.submit()
        # Set cookies
        self.session.cookies = cj
        # Get cid from url ?cid=...
        self.cid = re.search("\?cid=(.*)", br.geturl()).group(1)
        
        br.close()
        print("Logged in!")
    
    def checkSession(self):
        URL = "https://accesso.registroarchimede.it/archimede/home.seam"
        # Make a get request with session cookies
        result = self.session.get(URL, cookies=self.cookies)
        # If not redirected to login page, session is valid

        # From result.url, remove all from ?cid
        checkurl = result.url = re.sub("\?cid=.*", "", result.url)

        if checkurl == "https://accesso.registroarchimede.it/archimede/login.seam":
            self.login(self.username, self.password)
            return False
        else:
            return True

    # # Get "pagella"
    # def getSchoolReport(self):
    #     if self.checkSession():
    #         print(self.cid)
    #         URL = "https://accesso.registroarchimede.it/archimede/pagelle/superiore/docValutazione.pdf?docId=1&cid=" + self.cid
    #         # Make a get request with session cookies
    #         result = self.session.get(URL, cookies=self.cookies)
    #         return result.content

    def getStudentProfile(self):
        URL = "https://accesso.registroarchimede.it/archimede/alunno/riepilogoAlunno.seam"

        # Make a get request with session cookies
        result = self.session.get(URL, cookies=self.cookies)
        soup = BeautifulSoup(result.content, "html.parser")

        # get the first rf-p-b 
        div = soup.find("div", class_="rf-p-b")
        # Get all class valori
        valori = div.find_all("td", class_="valori")
        
        studentName = valori[0].text
        studentClass = valori[2].text
        studentAddess = valori[3].text
        studentSchoolYear = valori[4].text

        # Replace \n with space
        studentName = studentName.replace("\n", " ")
        studentClass = studentClass.replace("\n", " ")
        studentAddess = studentAddess.replace("\n", " ")
        studentSchoolYear = studentSchoolYear.replace("\n", " ")

        # Jsonify
        studentProfile = json.dumps({
            "name": studentName,
            "class": studentClass,
            "address": studentAddess,
            "schoolYear": studentSchoolYear
        })

        return studentProfile

    def getSchoolMessages(self):
        URL = "https://accesso.registroarchimede.it/archimede/circolari/CircolareListProf.seam"

        # Make a get request with session cookies
        result = self.session.get(URL, cookies=self.cookies)
        soup = BeautifulSoup(result.content, "html.parser")

        # Get trs
        trs = soup.find_all("tr", class_="ui-widget-content")
        dates = [tr.find_all("td")[1].text for tr in trs]
        objects = [tr.find_all("td")[2].text for tr in trs]
        senders = [tr.find_all("td")[3].text for tr in trs]

        # Replace \n with space
        dates = [date.replace("\n", " ") for date in dates]
        objects = [object.replace("\n", " ") for object in objects]
        senders = [sender.replace("\n", " ") for sender in senders]
        
        # Merge all lists. Key is the data and value is an array containing all messages for that date containing object and sender
        schoolMessages = {}
        for i in range(len(dates)):
            if dates[i] not in schoolMessages:
                schoolMessages[dates[i]] = []
            schoolMessages[dates[i]].append({
                "object": objects[i],
                "sender": senders[i]
            })

        # Jsonify
        schoolMessages = json.dumps(schoolMessages)
    
        return schoolMessages
    
    def getClassroomBoard(self):
        URL = "https://accesso.registroarchimede.it/archimede/docenti/elencoDocenti.seam"

        # Make a get request with session cookies
        result = self.session.get(URL, cookies=self.cookies)
        soup = BeautifulSoup(result.content, "html.parser")

        # Get trs
        trs = soup.find_all("tr", class_="ui-widget-content")

        images = [tr.find_all("td")[0].find("img").get("src") for tr in trs]
        subjects = [tr.find_all("td")[1].text for tr in trs]
        teachers = [tr.find_all("td")[2].text for tr in trs]
        coursesId = [tr.find_all("td")[3].find("a").get("href").split("=")[1].split("&")[0] for tr in trs]
        teachersId = [tr.find_all("td")[3].find("a").get("href").split("=")[2].split("&")[0] for tr in trs]

        # Replace \n with space
        images = [image.replace("\n", " ") for image in images]
        subjects = [subject.replace("\n", " ") for subject in subjects]
        teachers = [teacher.replace("\n", " ") for teacher in teachers]

        # Merge all lists. Index is the key
        classroomBoard = {}
        for i in range(len(images)):
            classroomBoard[i] = {
                "image": images[i],
                "subject": subjects[i],
                "teacher": teachers[i],
                "courseId": coursesId[i],
                "teacherId": teachersId[i]
            }

        # Jsonify
        classroomBoard = json.dumps(classroomBoard)

        return classroomBoard

    def getCourses(self):
        if self.checkSession():
            URL = "https://accesso.registroarchimede.it/archimede/alunno/riepilogoAlunno.seam"
            # Make a get request with session cookies
            result = self.session.get(URL, cookies=self.cookies)


            soup = BeautifulSoup(result.content, "html.parser")


            # Get the first div with have the class rf-tab-cnt
            div = soup.find("div", class_="rf-tab-cnt")
            # Get the first div inside previous div
            div = div.find("div").get("id")
        
            self.controlli = div

            print(self.controlli)

            # Make a post request with session cookies
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }

            payload='controlli=controlli&controlli%3ArichTabAlunni-value=altro&controlli%3Aj_idt164-value=alternanza'


            result = self.session.post(URL, data=payload, cookies=self.cookies, headers=headers)

            soup = BeautifulSoup(result.content, "html.parser")

            # Find all <tr> with class "rf-dt-r"
            trs = soup.find_all("tr", class_="rf-dt-r")
            # In a dict get the name of the course, the teacher and the corsoId (inside an <a> tag, inside the <td> tag)
            coursesNames = [tr.find("td", class_="rf-dt-c").text for tr in trs]
            coursesTeachers = [tr.find("td", class_="rf-dt-c").find_next_sibling("td").text for tr in trs]
            coursesIds = [tr.find("td", class_="rf-dt-c").find_next_sibling("td").find_next_sibling("td").text for tr in trs]
            
            # Combine coursesNames, coursesTeachers and coursesIds. Example:
            # {["Matematica", "Prof. Rossi", "123456"], ["Italiano", "Prof. Bianchi", "654321"]}
            courses = list(zip(coursesNames, coursesTeachers, coursesIds))
            # Convert to json
            courses = json.dumps(courses)

            return(courses)
    
    def getHomework(self, corsoId):
        if self.checkSession():
            if corsoId == None:
                return "Corso non trovato"
            
            if type(corsoId) == int:
                corsoId = str(corsoId)

            URL = "https://accesso.registroarchimede.it/archimede/compiti/compitiList.seam?corsoId=" + corsoId
            # Make a get request with session cookies
            result = self.session.get(URL, cookies=self.cookies)
            soup = BeautifulSoup(result.content, "html.parser")

            # Find all <tr> tags with class "rf-dt-r" and extract the text
            trs = soup.find_all("tr", class_="rf-dt-r")

            dates = [tr.find("td", class_="rf-dt-c").text for tr in trs]
            # Get second td of each tr
            tr_text = [tr.find_all("td")[1].text for tr in trs]
            # Remove \n
            tr_text = [tr.replace("\n", "") for tr in tr_text]
            # Combine dates and tr_text. If in the same date there are more than one homework, they will be in the same list
            homeworks = {}

            for i in range(len(dates)):
                if dates[i] in homeworks:
                    homeworks[dates[i]].append(tr_text[i])
                else:
                    homeworks[dates[i]] = [tr_text[i]]

            # Convert to json
            homework = json.dumps(homeworks)

            return(homework)

    def getSchoolGrades(self):
        if self.checkSession():
            URL = "https://accesso.registroarchimede.it/archimede/alunno/riepilogoAlunno.seam"
            # Make a get request with session cookies
            result = self.session.get(URL, cookies=self.cookies)
            soup = BeautifulSoup(result.content, "html.parser")
            # Find all <tr> with class "rf-dt-r"
            trs = soup.find_all("tr", class_="rf-dt-r")
            # Find all <td> with class "rf-dt-c"
            tds = soup.find_all("td", class_="rf-dt-c")
            # Get only the first <td> of each <tr>
            subjects = [td.find_all("td")[0].text for td in trs]
            # Remove \n
            subjects = [subject.replace("\n", "") for subject in subjects]

            # Find the grades date from <th> with class "rf-dt-shdr-c" and get text inside <center>. Skip the first <th>
            grades_dates = [th.find("center").text for th in soup.find_all("th", class_="rf-dt-shdr-c")[1:]]
            # Remove \n
            grades_dates = [grade_date.replace("\n", "") for grade_date in grades_dates]
            # Get len of grades_dates
            grades_dates_len = len(grades_dates)

            # Find all <td> with class "rf-dt-c" and get text. Every grades_dates_len skip a <td>
            grades = []
            for td in tds:
                # Get current index
                index = tds.index(td)
                if index == grades_dates_len:
                    # Remove <td>
                    tds.remove(td)
                    

            # Combine subjects, grades and grades_dates. Example:
            # {"Matematica": {"21/12": [8, 7]}, "Fisica": {"21/12": [8, 7]}}
            print(grades)
            grades_dict = dict(zip(subjects, [dict(zip(grades_dates, [grade.split("/") for grade in grade_list])) for grade_list in grades]))
            return(grades_dict)
