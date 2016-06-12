#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Views for security module
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from .forms import SecurityForm
from plinth import actions


ACCESS_CONF_FILE = '/etc/security/access.conf'
ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx (admin) (sudo):ALL'


def index(request):
    """Serve the security configuration form"""
    status = get_status(request)

    form = None

    if request.method == 'POST':
        form = SecurityForm(request.POST, initial=status, prefix='security')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status(request)
            form = SecurityForm(initial=status, prefix='security')
    else:
        form = SecurityForm(initial=status, prefix='security')

    return TemplateResponse(request, 'security.html',
                            {'title': _('Security'),
                             'form': form})


def get_status(request):
    """Return the current status"""
    return {'restricted_access': get_restricted_access_enabled()}


def _apply_changes(request, old_status, new_status):
    """Apply the form changes"""
    if old_status['restricted_access'] != new_status['restricted_access']:
        try:
            set_restricted_access(new_status['restricted_access'])
        except Exception as exception:
            messages.error(
                request,
                _('Error setting restricted access: {exception}')
                .format(exception=exception))
        else:
            messages.success(request, _('Updated security configuration'))


def get_restricted_access_enabled():
    """Return whether restricted access is enabled"""
    with open(ACCESS_CONF_FILE, 'r') as conffile:
        lines = conffile.readlines()

    for line in lines:
        if ACCESS_CONF_SNIPPET in line:
            return True

    return False


def set_restricted_access(enabled):
    """Enable or disable restricted access"""
    action = 'disable-restricted-access'
    if enabled:
        action = 'enable-restricted-access'
    actions.superuser_run('security', [action])
