from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import pandas as pd
import mysql.connector
import joblib
import os

# import model and processing code
app = Flask(__name__)
model = None
# pipeline = joblib.load('model.pkl')
app.secret_key = 'secret'

connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Natsudragnel157_',
    database='cuaca'
)

# rute index
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/service")
def service():
    return render_template("service.html")

# rute prediksi
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    model_exist = os.path.isfile('model.pkl')
    if request.method == 'POST':
        data = {
            'suhu': float(request.form['suhu']),
            'kelembaban': float(request.form['kelembaban']),
            'curah hujan': float(request.form['curah hujan']),
            'sinar matahari': float(request.form['sinar matahari']),
        }

        tanggal = request.form['tanggal']
        musim = request.form['musim']

        # Mengonversi tanggal dari string menjadi objek date
        input_date = datetime.strptime(tanggal, "%Y-%m-%d").date()

        # Mendefinisikan daftar nama bulan
        nama_bulan = [
            "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"
        ]

        # Mengubah format tanggal menjadi "dd NamaBulan yyyy"
        tgl_str = f"{input_date.day} {nama_bulan[input_date.month - 1]} {input_date.year}"

        global model
        if model_exist:
            # Memuat model dari file
            model = joblib.load('model.pkl')

            # Melakukan prediksi pada data baru
            prediction = model.predict(pd.DataFrame(data, index=[0]))

            return render_template('result.html', prediction=prediction[0], data=data, musim=musim, tanggal=tgl_str)
        else:
            return render_template('service.html')

    return render_template('service.html')



# rute tambah ulasan
@app.route('/ulasan', methods=['GET', 'POST'])
def ulasan():
    cursor = connection.cursor()
    rating = request.form['rating']
    pesan = request.form['pesan']

    # eksekusi query
    cursor.execute("INSERT INTO ulasan (rating, ulasan) VALUES (%s, %s)", (rating, pesan))
    connection.commit()

    return render_template('service.html')

@app.route('/delete_ulasan/<int:id>', methods=['GET', 'POST'])
def delete_ulasan(id):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM ulasan WHERE id = %s", (id,))
    connection.commit()

    # Alihkan ke halaman utama setelah penghapusan data
    return redirect('/read_ulasan')

@app.route('/read_ulasan')
def read_ulasan():
    if 'username' in session:
        username = session['username']
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM ulasan")
        ulasan = cursor.fetchall()

        return render_template('ulasan.html', username=username, ulasan=ulasan)
    else:
        return redirect('/login')

# rute tampil data cuaca (READ)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    model_exist = os.path.isfile('model.pkl')
    if request.method == 'POST':
        file = request.files['file']
        data = pd.read_csv(file)

        # Memisahkan fitur dan label
        features = data.iloc[:, :-1]
        labels = data.iloc[:, -1]

        # Membagi data menjadi data latih dan data uji
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42)

        # Melatih model naive bayes
        global model
        model = GaussianNB()
        model.fit(X_train, y_train)

        # Simpan model ke file
        joblib.dump(model, 'model.pkl')
        model_exist = True

        # Melakukan prediksi pada data uji
        y_pred = model.predict(X_test)

        # Menghitung metrik evaluasi
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred).tolist()

        return render_template('evaluation.html', accuracy=accuracy, precision=precision, recall=recall, f1=f1, confusion_matrix=cm, model_exist=model_exist)


    if 'username' in session:
        username = session['username']
        
        return render_template('admin.html', username=username, model_exist=model_exist)
    else:
        return redirect('/login')


# rute login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        print(username)
        print(password)

        if user:
            session['username'] = user[1]
            return redirect('/admin')
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    else:
        return render_template('login.html')


# rute logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)