import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from graphviz import Digraph
import uuid
import time
import pandas as pd
pos=""
df=pd.read_excel(r"HR.xlsx")
p_d=dict()
e_d=dict()
m_d=dict()
pe_d=dict()
d_d=dict()
df1=df.drop(['Eligibility'],axis=1)
df.drop(["Employee Id","Employee Name"],axis=1)
l1=list(df["Position"].unique())
for i in range(0,len(l1),1):
    p_d[l1[i]]=i+1
p_d['Senior Manager']=5
p_d['Team Leader']=3
for i in l1:
    df["Position"]=df["Position"].replace(i,p_d[i])
l2=list(df["Education"].unique())
for i in range(0,len(l2),1):
    e_d[l2[i]]=i+1
for i in l2:
    df["Education"]=df["Education"].replace(i,e_d[i])
l3=list(df["Manager's Feedback"].unique())
for i in range(0,len(l3),1):
    m_d[l3[i]]=i+1
for i in l3:
    df["Manager's Feedback"]=df["Manager's Feedback"].replace(i,m_d[i])
l4=list(df["Performance"].unique())
for i in range(0,len(l4),1):
    pe_d[l4[i]]=i+1
for i in l4:
    df["Performance"]=df["Performance"].replace(i,pe_d[i])
l5=list(df["Department"].unique())
for i in range(0,len(l5),1):
    d_d[l5[i]]=i+1
for i in l5:
    df["Department"]=df["Department"].replace(i,d_d[i])
df=df.drop(["Employee Id","Employee Name"],axis=1)
print(df.head())
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
X=df.iloc[:,0:7]
y=df.iloc[:,7]
model = Sequential()
model.add(Dense(8, input_dim=X.shape[1], activation='relu'))
model.add(Dense(14, activation='relu'))
model.add(Dense(1, activation='sigmoid'))
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(X, y, epochs=10, batch_size=32, validation_split=0.2)

if 'employees' not in st.session_state:
    st.session_state.employees = []

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Karthi23',
    'database': 'promotion'
}

QUERY1 = """
    SELECT E_Id, E_Name, Position
    FROM employee
    WHERE Position = 'General Manager'
    UNION ALL
    SELECT e.E_Id, e.E_Name, e.Position
    FROM employee e
    JOIN Employee eh ON e.E_id = eh.E_id
"""

def remove_employee(e_name,position):
    global pos
    pos=position
    connection = mysql.connector.connect(
        host="localhost",
        user='root',
        password='Karthi23',
        database='promotion'
    )
    cursor = connection.cursor()
    query = f"DELETE FROM employee WHERE E_Name=%s"
    cursor.execute(query, (e_name,))
    connection.commit()
    cursor.close()
    connection.close()


def recommendation(pos):
    po_l=['General Manager','HR Manager','Senior Manager','Supervisor','Team Leader','HR Assistant','Employee']
    for i in range(len(po_l)):
        if pos==po_l[i]:
            po_l=po_l[i:i+2]
            break
    import mysql.connector  
    connection = mysql.connector.connect(
        host="localhost",
        user='root',
        password='Karthi23',
        database='promotion'
    )
    sql_query = f"SELECT * FROM employee WHERE Position IN ({', '.join(['%s']*len(po_l))});"
    cursor = connection.cursor()
    cursor.execute(sql_query,po_l)
    result = cursor.fetchall()
    column_names=df1.columns.tolist()
    e_df = pd.DataFrame(result, columns=column_names)
    cursor.close()
    connection.close()
    X=e_df.iloc[:,2:10]
    X["Position"].replace(p_d,inplace=True)
    X["Education"].replace(e_d,inplace=True)
    X["Manager's Feedback"].replace(m_d,inplace=True)
    X["Performance"].replace(pe_d,inplace=True)
    X["Department"].replace(d_d,inplace=True)
    print(X.head())
    pred=model.predict(X)
    pred = (pred > 0.45).astype(int)
    e_df['Eligibility']=pred
    eligible=e_df["Eligibility"]>0
    eligible_df=e_df[eligible]
    eligible_df=eligible_df.drop(['Education','Experience','Certification','Eligibility'],axis=1)
    eligible_df.rename(columns={'Position':'Current_Position'},inplace=True)
    eligible_df.rename(columns={'Employee Id':'E_Id'},inplace=True)
    eligible_df.rename(columns={'Employee Name':'E_Name'},inplace=True)
    st.write(eligible_df) 
       
    name = st.text_input("Enter Name", key='name_input')

    if name:
        # Action to perform when the submit button is clicked
        st.write(f"Entered Name: {name}")
        promote(name,pos)

def promote(name, pos):
    global df
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user='root',
            password='Karthi23',
            database='promotion'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            query="Select position from employee where E_Name=%s"
            cursor.execute(query,(name,))
            position = cursor.fetchall()
            cursor.close()
            cursor = connection.cursor()
            sql_query = 'UPDATE employee SET Position=%s WHERE E_name=%s'
            
            cursor.execute(sql_query, [pos, name])
            connection.commit()

            # Check the number of affected rows
            num_rows_affected = cursor.rowcount

            if num_rows_affected > 0:
                st.success(f"Employee {name} promoted to {pos}.")
            else:
                st.warning(f"No rows affected. Employee {name} might not exist in the database.")
            

    except Error as e:
        st.error(f"Error updating employee details: {str(e)}")
    finally:
        cursor.close()
        cursor = connection.cursor()
        query="Select * from employee where E_Name=%s"
        cursor.execute(query,(name,))
        result = cursor.fetchall()
        employee=pd.DataFrame(result)
        print(employee.head())
        card = f'''
        <div style="border: 1px solid #000; padding: 10px; margin: 10px; width: 300px;">
        <h2><b>{employee.iloc[0,1]}<b></h2>
        <p><b>Experience:</b> {employee.iloc[0,4]}</p>
        <p><b>Performance:</b> {employee.iloc[0,5]}</p>
        <p><b>Current Position:</b> {position[0][0]}</p>
        <p><b>Promoted to </b> {employee.iloc[0,3]}</p>
        </div>
        '''
        st.markdown(card, unsafe_allow_html=True)
        if connection.is_connected():
            cursor.close()
            connection.close()
        text_placeholder = st.empty()
        for i in range(3):
            text_placeholder.text(f"Refreshing in {3 - i} seconds...")
            time.sleep(1)
        st.experimental_rerun()
    

def fetch_data_from_database():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Karthi23',
        database='promotion',
    )

    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute("SELECT E_name, position FROM employee")

        positions = {}

        rows = cursor.fetchall()

        for row in rows:
            employee_name = row[0]
            employee_position = row[1]

            if employee_position not in positions:
                positions[employee_position] = [employee_name]
            else:
                positions[employee_position].append(employee_name)

        cursor.close()
        connection.close()

        return positions
    else:
        print("Connection to MySQL database failed")


def display_hierarchy(positions):
    position_order = ['General Manager', 'HR Manager', 'Senior Manager', 'Supervisor', 'Team Leader', 'HR Assistant', 'Employee']

    st.title('Organization Hierarchy')

    for position in position_order:
        if position in positions:
            employees = positions[position]

            with st.expander(f"{position}"):
                for employee in employees:
                    unique_key = f"{position}-{employee}-{uuid.uuid4()}"

                    col1, col2 = st.columns([4, 1])
                    col1.markdown(f"*{employee}*", unsafe_allow_html=True)

                    with col2:
                        #Initialize session state 
                        
                        # Create a unique key for the remove button
                        remove_key = f"Remove-{position}-{employee}"
                        

                        if st.button(f"Remove {employee}", key=remove_key):
                        
                            positions[position].remove(employee)
                            st.success(f"{employee} removed from {position}")
                            st.empty()  
                            remove_employee(employee,position)


def fetch_employee_hierarchy():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(QUERY1)
    result = cursor.fetchall()
    conn.close()
    return result


def display_structure():
    st.title('Organization Structure')
    graph = Digraph(format='png')
    graph.node('CEO', 'CEO')
    graph.node('GM1', 'General Managers')
    graph.node('HRM1', 'HR Managers')
    graph.node('SM1', 'Senior Managers')
    graph.node('Sup1', 'Supervisors')
    graph.node('TL1', 'Team Leaders')
    graph.node('HRA1', 'HR Assistants')
    graph.node('Emp1', 'Employees')

    graph.edge('CEO', 'GM1')
    graph.edge('GM1', 'HRM1')
    graph.edge('HRM1', 'SM1')
    graph.edge('SM1', 'Sup1')
    graph.edge('Sup1', 'TL1')
    graph.edge('TL1', 'HRA1')
    graph.edge('HRA1', 'Emp1')

    return graph


def main(menu_selection='Structure'):
    st.title('Organization Management System')

    menu_selection = st.sidebar.selectbox("Menu", ("Structure", "Remove Employee","Recommend","Employee Data"))

    if menu_selection == 'Structure':
        st.title('Hierarchical Graph')
        graph = display_structure()
        st.graphviz_chart(graph.source)
        st.write("Hierarchical structure:")
        st.write("CEO --> General Managers")
        st.write("General Manager--> HR Managers")
        st.write("HR Manager--> Senior Managers")
        st.write("Senior Manager--> Supervisors")
        st.write("Supervisor--> Team Leaders")
        st.write("Team Leader --> HR Assistants")
        st.write("HR Assistant --> Employees")
    elif menu_selection == 'Remove Employee':
        positions = fetch_data_from_database() 
        display_hierarchy(positions)
    elif menu_selection == 'Employee Data':
        st.title("Corporate Company Employee Hierarchy")
        hierarchy_data = fetch_employee_hierarchy()
        hierarchy_df = pd.DataFrame(hierarchy_data)
        st.markdown('<h2>Employee Hierarchy</h2>', unsafe_allow_html=True)
        st.markdown('<h3>Data:</h3>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 16px">{hierarchy_df.to_html(index=False)}</div>', unsafe_allow_html=True)
    elif menu_selection=='Recommend':
        with st.form(key='position_form'):
            positions = ['General Manager', 'HR Manager', 'Senior Manager', 'Supervisor', 'Team Leader', 'HR Assistant', 'Employee']
            selected_position = st.radio("Select Position", positions)
            submit_button = st.form_submit_button(label='Submit')
            if submit_button:
                recommendation(selected_position)

if __name__ == "__main__":
    main()
