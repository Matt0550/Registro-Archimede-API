import requests
import re
from bs4 import BeautifulSoup
import mechanize
import http.cookiejar as cookielib 

class Api:
    
    def __init__(self, username, password):
        self.session = requests.session()
        self.cookies = self.session.cookies
        self.username = username
        self.password = password
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
            #self.login(self.username, self.password)
            self.login(self.username, self.password)
            return False
        else:
            return True

    
    def getHomework(self, corsoId):
        if self.checkSession():
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
            # Combine dates and tr_text. Example:
            # {["21/12", "Compito di prova"], ["21/12", "Compito di prova"]}
            homework = list(zip(dates, tr_text))
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
