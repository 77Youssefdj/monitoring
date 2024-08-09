from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory, current_app
import flask_login
import os
import sys
import json
import atexit

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from ipmon import db, scheduler, config
from ipmon.api import get_web_themes, get_polling_config, get_active_theme
from ipmon.database import Polling, WebThemes
from ipmon.forms import PollingConfigForm, UpdatePasswordForm, UpdateEmailForm
from ipmon.polling import update_poll_scheduler, add_poll_history_cleanup_cron
from ipmon.alerts import update_host_status_alert_schedule
from wtforms.validators import NumberRange
from ipmon.packet_quality import calculate_packet_quality



main = Blueprint('main', __name__)


@main.before_app_request
def webapp_init():
    app = current_app._get_current_object()
    if not database_configured():
        return
    init_schedulers()

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@main.route('/')
def index():
    if not os.path.exists(config['Database_Path']):
        return redirect(url_for('setup.setup'))
    return render_template('index.html', refresh_interval=10000)

@main.route("/account")
@flask_login.login_required
def account():
    password_form = UpdatePasswordForm()
    email_form = UpdateEmailForm()
    return render_template('account.html', password_form=password_form, email_form=email_form)

@main.route('/setTheme', methods=['GET', 'POST'])
@flask_login.login_required
def set_theme():
    if request.method == 'GET':
        return render_template('setTheme.html', themes=json.loads(get_web_themes()))
    elif request.method == 'POST':
        results = request.form.to_dict()
        try:
            for theme in json.loads(get_web_themes()):
                theme_obj = WebThemes.query.filter_by(id=int(theme['id'])).first()
                if theme_obj.id == int(results['id']):
                    theme_obj.active = True
                else:
                    theme_obj.active = False
            db.session.commit()
            flash('Successfully updated theme', 'success')
        except Exception as e:
            current_app.logger.error(f"Error updating theme: {e}")
            flash('Failed to update theme', 'danger')
    return redirect(url_for('main.set_theme'))

@main.route('/configurePolling', methods=['GET', 'POST'])
@flask_login.login_required
def configure_polling():
    form = PollingConfigForm()
    if request.method == 'GET':
        polling_config = json.loads(get_polling_config())
        return render_template('pollingConfig.html', polling_config=polling_config, form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            polling_config = Polling.query.first()
            try:
                if form.interval.data:
                    polling_config.poll_interval = int(form.interval.data)
                if form.retention_days.data:
                    polling_config.history_truncate_days = int(form.retention_days.data)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Error updating polling configuration: {e}")
                flash('Failed to update polling interval', 'danger')
                return redirect(url_for('main.configure_polling'))
            if form.interval.data:
                update_poll_scheduler(form.interval.data)
            flash('Successfully updated polling interval', 'success')
        else:
            for dummy, errors in form.errors.items():
                for error in errors:
                    flash(error, 'danger')
        return redirect(url_for('main.configure_polling'))
    
@main.route('/packet-quality')
@flask_login.login_required
def packet_quality():
    # Calculate metrics
    packet_loss, latency, jitter = calculate_packet_quality()

    # Debug print statements
    print(f"Packet Loss: {packet_loss}%")
    print(f"Latency: {latency} ms")
    print(f"Jitter: {jitter} ms")

    # Render template with values
    return render_template('packetQuality.html', packet_loss=packet_loss, latency=latency, jitter=jitter)

def init_schedulers():
    try:
        update_poll_scheduler(int(json.loads(get_polling_config())['poll_interval']))
        update_host_status_alert_schedule(int(json.loads(get_polling_config())['poll_interval']) / 2)
        add_poll_history_cleanup_cron()
        atexit.register(scheduler.shutdown)
    except Exception as e:
        current_app.logger.error(f"Error initializing schedulers: {e}")

def get_active_theme_path():
    if not database_configured():
        return '/static/css/darkly.min.css'
    return json.loads(get_active_theme())['theme_path']

def database_configured():
    return os.path.exists(config['Database_Path'])
