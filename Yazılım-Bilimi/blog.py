from flask import Flask,render_template,flash,redirect,url_for,session,logging,request 
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app=Flask(__name__)
app.secret_key="ybblog"

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ybblog"

app.config['MYSQL_CURSORCLASS'] = "DictCursor"
mysql=MySQL(app)





#Kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("İsim-Soyisim:",validators=[validators.Length(min=4,max=25),validators.DataRequired(message="İsim gir")])
    username = StringField("Kullanıcı adı:",validators=[validators.Length(min=10,max=25),validators.DataRequired(message="Kullanıcı adı gir")])
    email = StringField("E-mail gir:",validators=[validators.DataRequired(message="email gir"),validators.Email(message="Lütfen Geçerli bir Email adresi giriniz.")])
    password = PasswordField("Şifre belirle:",validators=[
        validators.Length(min=12,max=45),
        validators.DataRequired("Parola giriniz"),
        validators.EqualTo(fieldname="confirm",message="Parola aynı değil")
        ])
    confirm=PasswordField("Parola doğrula:",validators=[validators.DataRequired("doğrula")])
#KULLANICI GİRİŞ    DECORATOR
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapın...","danger")
            return redirect(url_for("login"))
    return decorated_function

#Kayıt olma   

@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        name = form.name.data
        username=form.username.data
        email=form.email.data
        password=form.password.data
        cursor=mysql.connection.cursor()
        sorgu="Insert into user(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla kayıt oldunuz...",category="success")
        

        return redirect(url_for("login"))
    else:

        return render_template("register.html",form=form)
#login işlemi
class LoginForm(Form):
    username=StringField("Kullanıcı adı:")
    password=PasswordField("Parola:")
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        password_entered=form.password.data

        cursor=mysql.connection.cursor()
        sorgu="Select*From user where username=%s"
        result=cursor.execute(sorgu,(username,))
        if result>0:
            data=cursor.fetchone()
            real_password=data["password"]
           
            if password_entered==real_password:
                flash("Başarıyla giriş yaptınız...","success")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Yanlış bilgi tekrar deneyiniz...","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",form=form)
#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()

    sorgu="Select*from articles where id=%s"

    result=cursor.execute(sorgu,(id,))
    
    if result>0:
        article=cursor.fetchone()
        print(article)
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")
#logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla çıkış yaptınız...","success")
    return redirect(url_for("index"))
@app.route("/")
def index():
   
    return render_template("index.html")
#DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()

    sorgu="Select*FROM articles WHERE author=%s"

    result=cursor.execute(sorgu,(session["username"],))
    if result>0 :
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    
    else:
        return render_template ("dashboard.html")
@app.route("/about")
def about():
    
    return render_template("about.html")
#Makale güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()

        sorgu="select*from articles where id=%s and author=%s"
        
        result=cursor.execute(sorgu,(id,session["username"]))

        if result==0:
            flash("Makale bulunmamakta veya bu işleme yetkiniz yok...","danger")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=ArticleForm()

            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)
            
    else:#post request kısmı
        form=ArticleForm(request.form)

        newTitle=form.title.data
        newContent=form.content.data
        
        sorgu2="Update articles Set title=%s,content=%s where id=%s"

        cursor=mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        cursor.close()
        
        flash("Makale başarıyla güncellendi...","success")
        return redirect(url_for("dashboard"))
#Makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()

    sorgu="Select*from articles where author=%s and id=%s"

    result=cursor.execute(sorgu,(session["username"],id))

    if result>0:
        sorgu2="Delete from articles where id =%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok...","danger")
        return redirect(url_for("index"))
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        
        cursor=mysql.connection.cursor()

        sorgu="Insert Into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Eklendi...","sucesss")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html",form=form)
#Makale Sayfası
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    
    sorgu="Select*FROM articles"

    result=cursor.execute(sorgu)

    if result>0:
        articles=cursor.fetchall()
        
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")

#arama url
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")

        cursor=mysql.connection.cursor()
        
        sorgu="Select*from articles where title like '%"+ keyword +"%'"

        result=cursor.execute(sorgu)
        if result==0:
            flash("Aranan kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()

            return render_template("articles.html",articles=articles)
#Makale form
class ArticleForm(Form):
    title=StringField("Makale Başlığı:",validators=[validators.Length(min=5,max=100),validators.DataRequired(message="Alanı girmek zorunlu...")])
    content=TextAreaField("Makale İçeriği:",validators=[validators.length(min=5)])
if __name__=="__main__":
    app.run(debug=True)
