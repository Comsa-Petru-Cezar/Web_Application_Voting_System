import secrets
import os
from flask import render_template, url_for, flash, redirect, request, abort
from Application.models import User, Election, Candidate, Votes
from Application.forms import RegForm, LogForm, UpdateAccForm, ElectionForm, CandidateForm
from Application import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required



@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    elections = Election.query.paginate(page=page, per_page=5)

    return render_template("home.html", elections=elections)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegForm()
    if form.validate_on_submit():
        hash_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hash_pass)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login',  methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LogForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_pg = request.args.get('next')
            return redirect(next_pg) if next_pg else redirect(url_for('home'))
        else:
            flash('Login failed', 'danger')
    return render_template('login.html', title='login', form=form)


@app.route('/logout',)
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/account', methods=['GET','POST'] )
@login_required
def account():
    form = UpdateAccForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.emil = form.email.data
        db.session.commit()
        flash('Account info updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    #img_file = url_for('static', filename='profil_pics/' + current_user.img)'''img_file=img_file,'''
    return render_template('account.html', title='account', form=form)


@app.route('/election/new', methods=['GET', 'POST'])
@login_required
def new_election():
    electionForm = ElectionForm()
    current_id = Election.get_next_valid_id()

    if electionForm.validate_on_submit():
        db.session.add(Election(id=current_id, title=electionForm.title.data, start_date=electionForm.start_date.data, end_date=electionForm.end_date.data, admin=current_user))
        db.session.commit()
        flash('Election created', 'success')
        CandidateForm.names = []
        return redirect(url_for('edit_election', election_id=current_id))

    return render_template('create_election.html', title='new election', election=electionForm, legend='New Election')

@app.route('/election_view/<int:election_id>', methods=['GET','POST'])
@login_required
def election_view(election_id):
    election_obj = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    return render_template('election_view.html', election=election_obj, candidates=candidates)


@app.route('/edit_election/<int:election_id>', methods=['GET', 'POST'])
@login_required
def edit_election(election_id):
    election_obj = Election.query.get_or_404(election_id)
    if election_obj.admin != current_user:
        return redirect(url_for('vote_election', election_id=election_id, candidate=0))

    if not election_obj.too_early():
        flash("Can't edit an election once it had started", 'warning')
        return redirect(url_for('election_view', election_id=election_id))

    candidates = Candidate.query.filter_by(election_id=election_id).all()
    candidateForm = CandidateForm()
    if candidateForm.validate_on_submit():
        if candidateForm.manually_validate_name(name=candidateForm.name, election=election_id):
            db.session.add(Candidate(name=candidateForm.name.data,votes=0, election_id=election_id))
            db.session.commit()
            flash('Candidate Added', 'success')
        else:
            flash('Candidate already exists', 'warning')
        return redirect(url_for('edit_election', election_id=election_id))
    return render_template('edit_election.html', election=election_obj,candidates=candidates, candidate=candidateForm)


@app.route('/vote_election/<int:election_id>/<int:candidate>', methods=['GET', 'POST'])
@login_required
def vote_election(election_id, candidate):
    election_obj = Election.query.get_or_404(election_id)
    if election_obj.too_early():
        flash("Election not yet open", 'warning')
        return redirect(url_for('election_view', election_id=election_id))

    if election_obj.too_late():
        flash("Election closed", 'warning')
        return redirect(url_for('election_view', election_id=election_id))
    if election_obj.already_voted(user_id=current_user.id, election_id=election_id):
        flash("You have already voted in this election", 'warning')
        return redirect(url_for('election_view', election_id=election_id))
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    return render_template('vote_election.html', election=election_obj, candidates=candidates, candidate=candidate)


@app.route('/commit_election/<int:election_id>/<int:candidate_id>', methods=['GET', 'POST'])
@login_required
def commit_election(election_id, candidate_id):
    if candidate_id == 0:
        return redirect(url_for('vote_election', election_id=election_id, candidate_id=candidate_id))
    election_obj = Election.query.get_or_404(election_id)
    if election_obj.already_voted(user_id=current_user.id, election_id=election_id):
        flash("You have already voted in this election", 'warning')
        return redirect(url_for('election_view', election_id=election_id))
    candidate = Candidate.query.filter_by(id=candidate_id).first()
    candidate.votes += 1
    db.session.add(Votes(election_id=election_id, user_id=current_user.id))
    db.session.commit()

    flash("Voted", 'success')
    return redirect(url_for('election_view', election_id=election_id))


@app.route('/election/delete/<int:election_id>', methods=['POST'])
@login_required
def delete_election(election_id):
    election = Election.query.get_or_404(election_id)
    if election.admin != current_user:
        return redirect(url_for('home'))
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    votes = Votes.query.filter_by(election_id=election_id).all()
    print(election)
    print(candidates)
    print(votes)
    if election.admin != current_user:
        abort(403)
    else:
        for v in votes:
            db.session.delete(v)
        for c in candidates:
            db.session.delete(c)
        db.session.delete(election)
        db.session.commit()
        flash('Election Deleted', 'success')
        return redirect(url_for('home'))


@app.route('/delete_candidate/<int:election_id>/<string:candidate_name>', methods=['GET','POST'])
@login_required
def delete_candidate(election_id, candidate_name):
    election = Election.query.get_or_404(election_id)
    if election.admin != current_user:
        return redirect(url_for('home'))
    else:
        candidate = Candidate.query.filter_by(name=candidate_name, election_id=election_id).first()

        db.session.delete(candidate)
        db.session.commit()
        flash('Candidate Removed', 'success')
        return redirect(url_for('edit_election', election_id=election_id))

