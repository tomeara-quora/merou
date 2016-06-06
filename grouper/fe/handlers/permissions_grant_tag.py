from grouper.constants import TAG_EDIT
from grouper.fe.forms import PermissionGrantTagForm
from grouper.fe.util import GrouperHandler
from grouper.models.audit_log import AuditLog
from grouper.models.permission import Permission
from grouper.models.public_key_tag import PublicKeyTag
from grouper.permissions import grant_permission_to_tag


class PermissionsGrantTag(GrouperHandler):
    def get(self, name=None):
        tag = PublicKeyTag.get(self.session, None, name)
        if not tag:
            return self.notfound()

        if not self.current_user.has_permission(TAG_EDIT, tag.name):
            return self.forbidden()

        form = PermissionGrantTagForm()
        form.permission.choices = [["", "(select one)"]]

        for perm in self.session.query(Permission).all():
            form.permission.choices.append([perm.name, "{} (*)".format(perm.name)])

        return self.render(
            "permission-grant-tag.html", form=form, tag=tag,
        )

    def post(self, name=None):
        tag = PublicKeyTag.get(self.session, None, name)
        if not tag:
            return self.notfound()

        if not self.current_user.has_permission(TAG_EDIT, tag.name):
            return self.forbidden()

        form = PermissionGrantTagForm(self.request.arguments)
        form.permission.choices = [["", "(select one)"]]

        for perm in self.session.query(Permission).all():
            form.permission.choices.append([perm.name, "{} (*)".format(perm.name)])

        if not form.validate():
            return self.render(
                "permission-grant-tag.html", form=form, tag=tag,
                alerts=self.get_form_alerts(form.errors)
            )

        permission = Permission.get(self.session, form.data["permission"])
        if not permission:
            return self.notfound()  # Shouldn't happen.

        success = grant_permission_to_tag(self.session, tag.id, permission.id,
                                    argument=form.data["argument"])

        if not success:
            form.argument.errors.append(
                "Permission and Argument already mapped to this tag."
            )
            return self.render(
                "permission-grant-tag.html", form=form, tag=tag,
                alerts=self.get_form_alerts(form.errors),
            )

        AuditLog.log(self.session, self.current_user.id, 'grant_permission_tag',
                     'Granted permission with argument: {}'.format(form.data["argument"]),
                     on_permission_id=permission.id, on_tag_id=tag.id)

        return self.redirect("/tags/{}?refresh=yes".format(tag.name))
