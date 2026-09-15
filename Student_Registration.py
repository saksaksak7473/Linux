import os
import time
import random
import json
import readchar

# ------------ clear screen ------------
def clear_screen():
    os.system("clear")

# ------------ colors ------------
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
PURPLE = "\033[34m"
BLUE = "\033[38;5;21m"
CYAN = "\033[36m"
WHITE = "\033[37m"
GREY = "\033[90m"
DIM_GREY = "\033[2m"

BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

RESET = "\033[0m"

# ------------ create an empty 'database file' if not have one ------------
if not os.path.exists("DataBase.json"):
    with open("DataBase.json", "w") as file:
        json.dump([], file)
        
# ------------ student class ------------
class Student:
    def __init__(self, name, id, sem, year):
        self.__name = name
        self.__id = id
        self.__sem = sem
        self.__year = year

        self.unit_list = [ # add more units here
            "Programming",
            "Physics 1",
            "Mathematics 2",
            "Writing and Research Skills",
            "Critical Thinking",
            "Reading",
            "Listening",
            "Public Speaking",
            "Cyber Security"
        ]
        
        self.groups = []
        self.units = []
        self.status = [False for _ in range(len(self.unit_list))]
        self.Add_Student()
        
    @property
    def name(self):
        return self.__name
    
    @property
    def id(self):
        return self.__id
    
    @property
    def sem(self):
        return self.__sem
    
    @property
    def year(self):
        return self.__year
    
    def register(self, group, unit):
        self.groups.append(group)
        self.units.append(unit)

    def Add_Student(self):
        with open("DataBase.json", "r") as file:
            students = json.load(file)

        isFound = False
        for student in students:
            if student["name"] == self.__name and student["id"] == self.__id:
                isFound = True
                break

        if not isFound:
            new_student = {
                "name": self.__name,
                "id": self.__id,
                "sem": self.__sem,
                "year": self.__year,
                "groups": [],
                "units": []
            }
            students.append(new_student)

        with open("DataBase.json", "w") as file:
            json.dump(students, file, indent = 4)

# ------------ checker ------------:
def get_name(prompt: str, error_msg: str, strings = None, isLogin = None):
    while True:
        string = error_msg
        isValid = False
        name = input(prompt).split()
        if len(name) == 2:
            name = name[0].strip().capitalize() + " " + name[1].strip().capitalize()
            if not name.isdigit():
                if isLogin:
                    isValid = True
                else:
                    with open("DataBase.json", "r") as file:
                        students = json.load(file)

                    for c_student in students:
                        if name == c_student["name"]:
                            string = f"{BOLD}{RED}Name is Already Taken!!{RESET}"
                            isValid = False
                            break
                        else: 
                            isValid = True
                
        if not isValid:
            clear_screen()
            if strings is not None: display(strings)
            print(f"{BOLD}{RED}{string}\n{RESET}")
        else:
            return name
            
def get_id(prompt: str, error_msg: str, strings = None, isLogin = None):
    while True:
        string = error_msg
        isValid = False
        id = input(prompt).strip()
        if id.isdigit() and len(id) == 9:
            temp = id[0:4]
            if temp == "7000":
                if isLogin:
                    isValid = True
                else:
                    with open("DataBase.json", "r") as file:
                        students = json.load(file)

                    for c_student in students:
                        if id == c_student["id"]:
                            string = f"{BOLD}{RED}ID is Already Taken!!{RESET}"
                            isValid = False
                            break
                        else: 
                            isValid = True
        
        if not isValid: 
            clear_screen()
            if strings is not None: display(strings)
            print(f"{BOLD}{RED}{string}\n{RESET}")
        else:
            return id
            
def get_int(prompt: str, error_msg: str, start: int, end: int, strings = None):
    while True:
        num = input(prompt).strip()
        if num.isdigit() and int(num) >= start and int(num) <= end:
            return num.lstrip("0")
        else: 
            clear_screen()
            if strings is not None: display(strings)
            print(f"{BOLD}{RED}{error_msg}\n{RESET}")

        
# ------------ loading screen ------------
def loading(prompt, strings = None):
    clear_screen()
    colors = [
        "\033[31m",
        "\033[32m",
        "\033[33m",
        "\033[34m",
        "\033[38;5;21m",
        "\033[36m"
    ]
    animation = ["|", "\\", "-", "/"]
    for _ in range(6):
        for frame in animation:
            if strings is not None: display(strings)
            print(f"{prompt}{BOLD}{random.choice(colors)}[{frame}]{RESET}")
            time.sleep(0.06)
            clear_screen()        

# ------------ bar loading ------------
def barLoading():
    clear_screen()
    num = 0
    pause = [0.5, 1]
    nums = [20, 15 ,25, 10, 5, 20, 5]
    random.shuffle(nums)
    nums.append(0)
    for i in nums:
        bar = "[" + "\u2593" * (int)(num / 5) + " " * (int)(20 - num / 5) + "]"
        print(f"{BOLD}Printing Your Registration Record: {bar} {num}%{RESET}")
        time.sleep(random.choice(pause))
        num += i
        clear_screen()

# ------------ display menu ------------
def display(strings):
    clear_screen()
    print(f"{BOLD}{GREEN}>> Authentication Page <<\n{RESET}")
    print(f"{UNDERLINE}" + " " * 38 + f"\n{RESET}")
    for i in range(len(strings)):
        print(strings[i])
    print(f"{UNDERLINE}" + " " * 38 + f"\n{RESET}")

# ------------ authentication page ------------     

def auth():
    error_msg = None
    isLogin = False
    while True:
        selected = 0
        while True:
            clear_screen()
            options = [
                "Login",
                "Signin",
                "Exit"
            ]
            print(f"{BOLD}{GREEN} >> Authentication Page <<\n{RESET}")
            OptDis(options, selected, error_msg)

            key = readchar.readkey()

            if key == 'w':
                selected -= 1
                if selected < 0:
                    selected = len(options) - 1

            if key == 's':
                selected += 1
                if selected > len(options) - 1:
                    selected = 0

            if key == '\n' or key == '\r':
                if selected == 0:
                    isLogin = True
                    break
                elif selected == 2: return None, None, None, None, False 
                break

        while True:
            strings_1 = [
                "1. Student Name: ",
                "2. Student ID: "
            ]
            # name:
            clear_screen()
            display(strings_1)
            name = get_name(f"{DIM_GREY}Enter Your Student Name (e.g. Song Vansak): {RESET}", "Invalid Student Name!!", strings_1, isLogin)
            strings_1[0] += f"{BOLD}{BLUE}{name}{RESET}"
            
            # id:
            clear_screen()
            display(strings_1)
            id = get_id(f"{DIM_GREY}Enter Your Student ID (e.g. 7000XXXXX): {RESET}", "Invalid Student ID!!", strings_1, isLogin)
            strings_1[1] += f"{BOLD}{BLUE}{id}{RESET}"
            
            clear_screen()
            display(strings_1)

            print(f"{DIM_GREY}Press 'Enter' to Continue or 'q' to Go Back: {RESET}")
            key = readchar.readkey()
            if key == 'q': 
                isLogin = False
                break
            
            if not isLogin:
                loading(f"Welcome to our Grouping Registration App, {CYAN}{name} (ID: {id})!{RESET}\n\nLoading: ", strings_1)
                strings_2 = [
                    "3. Your Semester: ",
                    "4. Your Year: "
                ]
                # semester:
                clear_screen()
                display(strings_2)
                sem = get_int(f"{DIM_GREY}Enter Your Semester (e.g. 1, 2, 3): {RESET}", "Invalid Semester!!", 1, 10, strings_2)
                strings_2[0] += f"{BOLD}{BLUE}{sem}{RESET}"
                
                # year:
                clear_screen()
                display(strings_2)
                year = get_int(f"{DIM_GREY}Enter Your Year (e.g. 2026): {RESET}", "Invalid Year!!", 2025, 2030, strings_2)
                strings_2[1] += f"{BOLD}{BLUE}{year}{RESET}"
                
                clear_screen()
                display(strings_2)
        
                print(f"{DIM_GREY}Press 'Enter' to Continue or 'q' to Go Back: {RESET}")
                key = readchar.readkey()
                if key == 'q':
                    isLogin = False
                    break
                
                loading(f"Thank you for your input. You are registering for Trimester {CYAN}{sem}F-{year}!{RESET}\n\nLoading: ", strings_2)

                return name, id, sem, year, True

            else:
                loading(f"Checking Database for: {CYAN}{name} and ID: {id} ... {RESET}", strings_1)
                with open("DataBase.json", "r") as file:
                    students = json.load(file)
                    for c_student in students:
                        if c_student["name"] == name and c_student["id"] == id:
                            sem, year = c_student["sem"], c_student["year"]
                            return name, id, sem, year, True
                        
                error_msg = f"{BOLD}{RED}Invalid Name or ID!{RESET}"
                break

# ------------ options display ------------
def OptDis(options, selected, error_msg = None, student = None, other_options = None, list = None, unit_list = None):
    WIDTH = 35
    colors = [
        "\033[32m",
        "\033[31m"
    ]
    if student is not None:
        if len(student.units) == len(student.unit_list) and other_options is not None:
            options[len(options) - len(other_options) + 2] = f"{GREY}{options[len(options) - len(other_options) + 2]:<{WIDTH}}{RESET}"
        for i in range(len(options)):
            if options[i] in student.units:
                options[i] = f"{GREY}{options[i]:<{WIDTH}}{RESET}"
        if list is not None:
            for i, unit in enumerate(student.units):
                if unit in list:
                    options[i] = f"{GREY}{options[i]:<{WIDTH}}{RESET}"
        if unit_list is not None:
            for i, unit in enumerate(unit_list):
                if unit in list:
                    options[i] = f"{GREY}{options[i]:<{WIDTH}}{RESET}"
                    
    highlighted = f"{CYAN}{BOLD}{colors[0]} {options[selected]:<{WIDTH}}<{RESET}" if selected != len(options) - 1 else f"{CYAN}{BOLD}{colors[1]} {options[selected]:<{WIDTH}}<{RESET}"
    options[selected] = highlighted

    print(f"{UNDERLINE}" + " " * 37 + f"\n{RESET}")
    for i in range(len(options)):
        print(options[i])
    print(f"{UNDERLINE}" + " " * 37 + f"\n{RESET}")
    if error_msg is not None: print(f"{RED}{BOLD}{error_msg}{RESET}\n")
    print(f"{DIM_GREY} press 'W / S' to Navigate, 'Enter' to Continue{RESET}")

# ------------ main page ------------
def mainPage(student):
    clear_screen()
    selected = 0
    error_msg = None
    while True:
        clear_screen()
        options = [
            "Register for Grouping",
            "View/Print Grouping Record",
            "Log out",
            "Exit"
        ]
        
        print(f"{BOLD}{PURPLE}>> Group Registration Main Page <<\n{RESET}")
        OptDis(options, selected, error_msg)

        key = readchar.readkey()
        
        if key == 's':
            selected += 1
            if selected > len(options) - 1:
                selected = 0  
        elif key == 'w':
            selected -= 1
            if selected < 0:
                selected = len(options) - 1
        elif key == '\r' or key == '\n':
            if len(student.units) == 0 and selected == 1:
                error_msg = f"{BOLD}{RED}You Have Not Registered Using Menu 1 Above!!{RESET}"
            else:
                error_msg = None
                break
        
    return selected

# ------------ registration module ------------
def GroupPage(student):
    clear_screen()
    selected = 0
    while True:
        clear_screen()
        options = [
            "1E1",
            "1E2",
            "1E3",
            "1E4",
            "Exit to Main Page"
        ]
        print(f"{BOLD}{PURPLE}>> Welcome to Group Registration Module, {student.name}! <<\n{RESET}")
        print("Choose ONE of the following groupings:")
        OptDis(options.copy(), selected)
        
        key = readchar.readkey()
        
        if key == 'w':
            selected -= 1
            if selected < 0:
                selected = len(options) - 1
        if key == 's':
            selected += 1
            if selected > len(options) - 1:
                selected = 0
        if key == '\n' or key == '\r':
            temp_g = options[selected].strip()
            break
        
    return selected, temp_g

# ------------ Group view ------------
def GroupView(student):
    error_msg = None
    while True:
        isFound = False
        with open("DataBase.json", "r") as file:
            students = json.load(file)

        for c_student in students:
            for group in c_student["groups"]:
                if group == temp_g:
                    isFound = True
                    break
            if isFound: break
        if not isFound: 
            error_msg = error_msg = f"{BOLD}{RED}No Student Registered in This Group Yet!!{RESET}"
            break

        clear_screen()
        print(f"{BOLD}{BLUE}Here are the Students in group {temp_g}:{RESET}\n")
        print(f"{UNDERLINE}" + " " * 37 + f"{RESET}\n")

        for c_student in students:
            for group in c_student["groups"]:
                if group == temp_g:
                    error_msg = None
                    isFound = True
                    if student.name == c_student["name"]: print(f"+ Name: {GREEN}{BOLD}{c_student["name"]} (YOU){RESET} Registered: ")
                    else: print(f"+ Name: {BOLD}{CYAN}{c_student["name"]}{RESET} Registered: ")
                    for g, unit in zip(c_student["groups"], c_student["units"]):
                        if g == temp_g:
                            print(f" - {unit}")

                    print()
                    break

        print(f"{UNDERLINE}" + " " * 37 + f"{RESET}\n")
        print(f"{DIM_GREY}Press 'Enter' to Continue: {RESET}")
        key = readchar.readkey()

        if key in ('\r', '\n'): break
    return error_msg

# ------------ units page ------------
def UnitPage(temp_g, student):
    clear_screen()
    selected = 0
    error_msg = None
    multi_sel = False
    sel_list = []
    other_options = [
        "",
        "Multiple Units Selection",
        "All / Remaining Units Above",
        f"Student List for Group {temp_g}",
        "Go Back"
    ]
    while True:
        isValid = False
        clear_screen()
        options = [
            unit for unit in student.unit_list
        ]
        for opt in other_options:
            options.append(opt)
        
        print(f"{BOLD}{PURPLE}>> Units Selection Page <<\n{RESET}")
        print(f"Please Select the Following Units for Group {BOLD}{CYAN}{temp_g}{RESET}:")
        OptDis(options.copy(), selected, error_msg, student, other_options, sel_list, student.unit_list)
        
        key = readchar.readkey()
        
        if key == 'w':
            selected -= 1
            if selected < 0:
                selected = len(options) - 1
            elif selected == len(options) - len(other_options):
                selected -= 1
        if key == 's':
            selected += 1
            if selected > len(options) - 1:
                selected = 0
            elif selected == len(options) - len(other_options):
                selected += 1
        if key == '\n' or key == '\r':
            # Options for selecting individual unit
            if selected < len(options) - len(other_options):
                if multi_sel:
                    for group, unit in zip(student.groups, student.units):
                        if options[selected] == unit:
                            error_msg = f"\n{RED}{BOLD}You have Previously Registered for unit {unit} for {group}!{RESET}"
                            break
                    if student.unit_list[selected] not in student.units: sel_list.append(student.unit_list[selected])
                else:
                    for group, unit in zip(student.groups, student.units):
                        if options[selected] == unit:
                            error_msg = f"\n{RED}{BOLD}You have Previously Registered for unit {unit} for {group}!{RESET}"
                            break
                    if options[selected] not in student.units:
                        error_msg = None
                        isValid = True
                        student.register(temp_g, options[selected])
                        student.status[selected] = True
                        with open("DataBase.json", "r") as file:
                            students = json.load(file)
                            for c_student in students:
                                if student.name == c_student["name"] and student.id == c_student["id"]:
                                    c_student["groups"].append(temp_g)
                                    c_student["units"].append(options[selected])

                        with open("DataBase.json", "w") as file:
                            json.dump(students, file, indent = 4)
            # multiple units selection
            elif selected == len(options) - 4:
                if other_options[1] == "Multiple Units Selection" :
                    other_options[1], other_options[4] = "Confirm", "Cancel"
                    multi_sel = True
                else: 
                    other_options[1], other_options[4] = "Multiple Units Selection", "Go Back"
                    multi_sel = False

                    if not sel_list:
                        error_msg = f"{BOLD}{RED}You Didn't Register Any Unit!!{RESET}"
                    else: 
                        isValid = True
                        error_msg = None

                    for i, unit in enumerate(student.unit_list):
                        if unit in sel_list:
                            student.register(temp_g, unit)
                            student.status[i] = True

                    with open("DataBase.json", "r") as file:
                        students = json.load(file)

                        for c_student in students:
                            if c_student["name"] == student.name and c_student["id"] == student.id:
                                for unit in sel_list:
                                    c_student["units"].append(unit)
                                    c_student["groups"].append(temp_g)

                    with open("DataBase.json", "w") as file:
                        json.dump(students, file, indent = 4)
                    
            # Option for display student list
            elif selected == len(options) - 2:
                error_msg = GroupView(student)

            # Option for exit the page     
            elif selected == len(options) - 1:
                if not multi_sel:
                    break
                else:
                    other_options[1], other_options[4] = "Multiple Units Selection", "Go Back"
                    error_msg = None
                    multi_sel = False
                    sel_list = []

            # option for selecting all the unit
            else:
                if len(student.unit_list) == len(student.units):
                    isValid = False
                    error_msg = f"\n{RED}{BOLD}No Unit is Left To Register!{RESET}"

                for unit in student.unit_list:
                    if unit not in student.units:
                        isValid = True
                        student.register(temp_g, unit)
                        for i in range(len(student.status)):
                            student.status[i] = True

                with open("DataBase.json", "r") as file:
                    students = json.load(file)
                    for c_student in students:
                        if student.name == c_student["name"] and student.id == c_student["id"]:
                            c_student["groups"] = student.groups
                            c_student["units"] = student.units
                            break

                with open("DataBase.json", "w") as file:
                    json.dump(students, file, indent = 4)

        if isValid:
            error_msg = f"{BOLD}{GREEN}Registered!!{RESET}"
            sel_list = []

# ------------record page ------------
def RecordPage(student):
    clear_screen()
    selected = 0
    WIDTH = 20
    while True:
        if not student.units: return 2
        clear_screen()
        options = [
            "Print My Grouping Record",
            "Modify Registration Record",
            "Exit to Main Page"
        ]
        print(f"{BOLD}{PURPLE}>> Welcome to Grouping Record <<\n{RESET}")
        print("Here are your Registered Groupings: ")
        print(f"{UNDERLINE}" + " " * 37 + f"\n{RESET}")
        print(f"- {f'Trimester:':<{WIDTH}} {BOLD}{BLUE}{student.sem}F-{student.year}{RESET}")
        print(f"- {'Student Name:':<{WIDTH}} {BOLD}{BLUE}{student.name}{RESET}")
        print(f"- {f'Student ID:':<{WIDTH}} {BOLD}{BLUE}{student.id}{RESET}\n")
        print(f"{BOLD}" + "=" * 37 + f"{RESET}")
        print(f"{BOLD}{f'UNITS':<{WIDTH + 9}}GROUPING{RESET}")
        print(f"{BOLD}" + "=" * 37 + f"{RESET}")
        for unit, group in zip(student.units, student.groups):
            print(f"{unit:<{WIDTH + 14}}{group}")
        print(f"{BOLD}" + "=" * 37 + f"{RESET}\n")
        OptDis(options, selected)
        
        key = readchar.readkey()
        
        if key == 'w':
            selected -= 1
            if selected < 0:
                selected = len(options) - 1
        if key == 's':
            selected += 1
            if selected > len(options) - 1:
                selected = 0
        if key == '\n' or key == '\r':
            break
            
    return selected

# ------------ modify record ------------
def ModRec(student):
    WIDTH = 30
    selected = 0
    error_msg = None
    multi_del = False
    del_list = []
    other_options = [
        "",
        "Multiple Delete",
        "Go Back"
    ]
    while True:
        table = []
        for unit, group in zip(student.units, student.groups):
            table.append(f"{unit:<{WIDTH}}{group}")

        for option in other_options:
            table.append(option)

        clear_screen()
        print(f"{BOLD}{RED}>> Modification Record Page <<{RESET}")
        print(f"{BOLD}{UNDERLINE}" + " " * 37 + f"{RESET}\n")
        print(f"{BOLD}{f'UNITS':<{WIDTH - 1}}GROUPING{RESET}")
        OptDis(table, selected, error_msg, student, None, del_list)

        key = readchar.readkey()

        if key == 'w':
            selected -= 1
            if selected < 0:
                selected = len(table) - 1
            elif selected == len(table) - len(other_options):
                selected -= 1

        if key == 's':
            selected += 1
            if selected > len(table) - 1:
                selected = 0
            elif selected == len(table) - len(other_options):
                selected += 1

        if key == '\r' or key == '\n':
            with open("DataBase.json", "r") as file:
                students = json.load(file)

            # Exit
            if selected == len(table) - 1:
                if multi_del:
                    other_options[1], other_options[2] = "Multiple Delete", "Go Back"
                    multi_del = False
                    error_msg = None
                    del_list = []
                else:
                    break

            # Multiple Delete
            elif selected == len(table) - 2: 
                if other_options[1] == "Multiple Delete":
                    other_options[1], other_options[2] = "Confirm", "Cancel"
                    multi_del = True
                else:
                    other_options[1], other_options[2] = "Multiple Delete", "Go Back"
                    multi_del = False

                    if not del_list:
                        error_msg = f"{BOLD}{RED}Nothing is Selected!!{RESET}"
                    else: error_msg = None

                    for c_student in students:
                        if c_student["name"] == student.name and c_student["id"] == student.id:
                            for unit, group in zip(student.units, student.groups):
                                if unit in del_list:
                                    c_student["units"].remove(unit)
                                    c_student["groups"].remove(group)

                    units, groups = student.units.copy(), student.groups.copy()
                    for i, (unit, group) in enumerate(zip(units, groups)):
                        if unit in del_list:
                            student.units.remove(unit)
                            student.groups.remove(group)
                            student.status[i] = False

                    del_list = []

            # Individual Delete
            else:
                if multi_del:
                    if student.units[selected] not in del_list:
                        error_msg = None
                        del_list.append(student.units[selected])
                    else:
                        error_msg = f"{RED}{BOLD}Already Selected!!{RESET}"
                else:
                    error_msg = None
                    student.units.remove(student.units[selected])
                    student.groups.remove(student.groups[selected])
                    student.status[selected] = False

                    for c_student in students:
                        if c_student["name"] == student.name and c_student["id"] == student.id:
                            c_student["units"].remove(c_student["units"][selected])
                            c_student["groups"].remove(c_student["groups"][selected])
                            break

                    selected = 0    

            with open("DataBase.json", "w") as file:
                json.dump(students, file, indent = 4)

        if not student.units:
            break

# ------------ main execution part ------------
running = True

if __name__ == '__main__':
    while running:
        name, id, sem, year, running = auth()
        if not running: 
            clear_screen()
            break
        student = Student(name, id, sem, year)
        with open("DataBase.json", "r") as file:
            students = json.load(file)
            for c_student in students:
                if c_student["name"] == name:
                    student.groups = c_student["groups"]
                    student.units = c_student["units"]
                    break

        while True:
            opt = mainPage(student)
            if opt == 0:
                loading("Loading Group Registration Module: ")
                while True:
                    opt, temp_g = GroupPage(student)
                    if opt >= 0 and opt < 4:
                        while True:
                            opt = UnitPage(temp_g, student)
                            break
                    else:
                        loading("Returning to Main Page: ")
                        break
                    if opt == 5: break
            elif opt == 1 and student.units:
                loading("Loading Grouping Record Module: ")
                while True:
                    opt = RecordPage(student)
                    if opt == 0:
                        barLoading()
                    elif opt == 1:
                        loading("Loadong Modification Page: ")
                        ModRec(student)
                    elif opt == 2:
                        loading("Returning to Main Page: ")
                        break
            elif opt == 2:
                loading("Returning to Authentication Page: ")
                break
            else: 
                clear_screen()
                running = False
                break
        if not running: break