import requests
import sqlite3
import time
import threading

def send_message(kcmc, name, xf, jd, bfzcj):
    token_url = f"https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
    toekn_headers = {
        "Content-Type": "application/json"
    }
    token_data = {
        "app_id": "cli_a58d5eca27bf100d",
        "app_secret": "05bW6O9WwfCQQV5bRMHIYbqhQwzVzLFL",
    }
    token_response = requests.post(token_url, headers=toekn_headers, json=token_data)
    tenant_access_token = token_response.json().get('tenant_access_token')
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    card_body = "{\"type\":\"template\",\"data\":{\"template_id\":\"AAqFFdh1bM4C9\",\"template_version_name\":\"1.0.0\",\"template_variable\":{\"kcmc\":\"" + kcmc + "\",\"name\":\"" + name + "\",\"xf\":\"" + xf + "\",\"jd\":\"" + jd + "\",\"bfzcj\":\"" + bfzcj +"\"}}}"
    data = {
        "receive_id": "ou_2b6a907c28739ded2d6f0d5038301f28",
        "content": card_body,
        "msg_type": "interactive"
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def get_grade(username, password):
    login_url = "https://myjw.zeabur.app/login"
    login_data = {
        "username": username,
        "password": password
    }
    login_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    login_response = requests.post(login_url, headers=login_headers, data=login_data)
    JSESSIONID = login_response.json().get('JSESSIONID')
    grade_url = "https://myjw.zeabur.app/grade"
    rxnj = username[:4]
    xnm_list = [rxnj, str(int(rxnj) + 1), str(int(rxnj) + 2), str(int(rxnj) + 3)]
    xqm_list = ["3", "12"]
    result = []
    for xnm in xnm_list:
        for xqm in xqm_list:
            grade_data = {
                "JSESSIONID": JSESSIONID,
                "xnm": xnm,
                "xqm": xqm
            }
            grade_headers = {
                "Content-Type": "application/json",
            }
            grade_response = requests.post(grade_url, headers=grade_headers, json=grade_data)
            grade_list = grade_response.json().get('items')
            print(grade_list)
            if grade_list is not None:
                for grade in grade_list:
                    result.append(grade)
    return result

def get_all_users_grade():
    all_users = requests.get("https://myjw.zeabur.app/users").json().get("users")
    # 对相同username的用户进行去重
    users = []
    for user in all_users:
        item = {
            "username": user.get("username"),
            "password": user.get("password")
        }
        if item not in users:
            users.append(item)
    users_info = []
    for user in users:
        grades = get_grade(user.get("username"), user.get("password"))
        users_info.append({
            "username": user.get("username"),
            "password": user.get("password"),
            "grades": grades
        })
    return users_info

def init_db():
    conn = sqlite3.connect('grades.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            kcmc TEXT NOT NULL,
            xf TEXT NOT NULL,
            jd TEXT NOT NULL,
            bfzcj TEXT NOT NULL,
            UNIQUE(username, kcmc)
        )
    ''')
    conn.commit()
    conn.close()

def store_grades(users_info):
    conn = sqlite3.connect('grades.db')
    cursor = conn.cursor()
    updated_entries = []
    
    for user in users_info:
        username = user['username']
        for grade in user['grades']:
            kcmc = grade.get('kcmc', '')
            xf = grade.get('xf', '')
            jd = grade.get('jd', '')
            bfzcj = grade.get('bfzcj', '')
            name = grade.get('xm', '')
            
            cursor.execute("SELECT bfzcj FROM grades WHERE username=? AND kcmc=?", (username, kcmc))
            existing_entry = cursor.fetchone()
            
            if existing_entry is None:
                cursor.execute("INSERT INTO grades (username, kcmc, xf, jd, bfzcj) VALUES (?, ?, ?, ?, ?)", 
                               (username, kcmc, xf, jd, bfzcj))
                updated_entries.append((name, kcmc, xf, jd, bfzcj))
            else:
                existing_bfzcj = existing_entry[0]
                if existing_bfzcj != bfzcj:
                    cursor.execute("UPDATE grades SET xf=?, jd=?, bfzcj=? WHERE username=? AND kcmc=?", 
                                   (xf, jd, bfzcj, username, kcmc))
                    updated_entries.append((name, kcmc, xf, jd, bfzcj))
    
    conn.commit()
    conn.close()
    return updated_entries

def check_and_update():
    while True:
        users_info = get_all_users_grade()
        updated_entries = store_grades(users_info)
        
        for entry in updated_entries:
            name, kcmc, xf, jd, bfzcj = entry
            send_message(kcmc, name, xf, jd, bfzcj)
        
        time.sleep(300)  # 5分钟检查一次

def main():
    init_db()
    thread = threading.Thread(target=check_and_update)
    thread.daemon = True
    thread.start()
    print("后台线程已启动，定期检查成绩更新")
    
    while True:
        time.sleep(3600)  # 主线程保持运行

if __name__ == "__main__":
    main()
