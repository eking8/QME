# pylint: disable=abstract-method
"""
cli.app.android.android_snippets

Android code snippets.
"""

from cli.app import code_snippet
from cli.app import file_manager
from cli.app.android import android_helpers


class AndroidManifestSnippet(code_snippet.CodeSnippet):
    """Base class for snippets added to AndroidManifest.xml"""

    def __init__(self, app_config, app):
        super().__init__(app_config, app)
        self.path = app_config.android_manifest_path


class MainActivitySnippet(code_snippet.CodeSnippet):
    """Base class for snippets added to the Main Activity."""

    def __init__(self, app_config, app):
        super().__init__(app_config, app)
        self.path = app_config.main_activity_path


class AppGradleSnippet(code_snippet.CodeSnippet):
    """Base class for snippets added to App build.gradle file."""

    def __init__(self, app_config, app):
        super().__init__(app_config, app)
        self.path = app_config.app_gradle_path


class ProjectGradleSnippet(code_snippet.CodeSnippet):
    """Base class for snippets added to Project build.gradle file."""

    def __init__(self, app_config, app):
        super().__init__(app_config, app)
        self.path = app_config.project_gradle_path


class FritzCustomModelServiceSnippet(AndroidManifestSnippet):
    """Adds FritzCustomModelService. """

    def __init__(self, app_config, app):
        super().__init__(app_config, app)
        self.path = app_config.android_manifest_path

    @property
    def is_added(self):
        contents = self.path.read_text()
        return "ai.fritz.core.FritzCustomModelService" in contents

    def add(self):
        snippet = """
        <service
            android:name="ai.fritz.core.FritzCustomModelService"
            android:exported="true"
            android:permission="android.permission.BIND_JOB_SERVICE" />\n
        """
        modified = file_manager.insert_before(self.path, "</application>", snippet)
        self.path.write_text(modified)


class InternetPermissionsSnippet(AndroidManifestSnippet):
    """Adds internet permissions to manifest."""

    @property
    def is_added(self):
        contents = self.path.read_text()
        return "android.permission.INTERNET" in contents

    def add(self):
        snippet = """
    <uses-permission android:name="android.permission.INTERNET" />
        """
        modified = file_manager.insert_before(self.path, "<application", snippet)
        self.path.write_text(modified)


class ImportFritzSnippet(MainActivitySnippet):
    """Import Fritz in main activity."""

    @property
    def is_added(self):
        contents = self.path.read_text()
        return "import ai.fritz.core.Fritz;" in contents

    def add(self):
        modified = file_manager.insert_after(
            self.path, "package", "import ai.fritz.core.Fritz;\n"
        )
        self.path.write_text(modified)


class ConfigureFritzSnippet(MainActivitySnippet):
    """Adds Fritz.configure call in Main Activity."""

    @property
    def is_added(self):
        contents = self.path.read_text()
        return "Fritz.configure" in contents

    def add(self):
        configure = file_manager.add_indentation(
            2
        ) + 'Fritz.configure(this, "{api_key}");'.format(api_key=self.app.api_key)
        modified = file_manager.insert_line_at_block_end(
            self.path, "void onCreate", configure
        )
        self.path.write_text(modified)

    @property
    def is_updated(self):
        if not self.is_added:
            return True

        api_key = android_helpers.find_fritz_api_key(self.path)
        return api_key == self.app.api_key

    def update(self):
        api_key = android_helpers.find_fritz_api_key(self.path)
        text = self.path.read_text()
        updated = text.replace(api_key, self.app.api_key)
        self.path.write_text(updated)


class AddBuildDependencies(AppGradleSnippet):
    """Add Fritz build dependendies to App Gradle file."""

    @property
    def is_added(self):
        contents = self.path.read_text()
        return "ai.fritz:core" in contents

    def add(self):
        text = """
    implementation 'ai.fritz:core:+'
    implementation 'ai.fritz:vision:+'
        """
        modified = file_manager.insert_line_at_block_end(
            self.path, "dependencies", text
        )
        self.path.write_text(modified)


class AddRenderscript(AppGradleSnippet):
    """Enable renderscript in the app Gradle file."""

    @property
    def is_added(self):
        contents = self.path.read_text()
        return (
            "renderscriptTargetApi" in contents
            and "renderscriptSupportModeEnabled" in contents
        )

    def add(self):
        text = """
        renderscriptTargetApi 21
        renderscriptSupportModeEnabled true
        """
        modified = file_manager.insert_line_at_block_end(
            self.path, "defaultConfig", text
        )
        self.path.write_text(modified)


class AddProjectBuildDependencies(ProjectGradleSnippet):
    """Add Fritz repository to Project Gradle file."""

    @property
    def is_added(self):
        contents = self.path.read_text()
        repo = "https://raw.github.com/fritzlabs/fritz-repository/master"
        return repo in contents

    def add(self):
        lines = self.path.open().readlines()
        start, end = file_manager.find_block_indexes(lines, "allprojects")

        if start is None or end is None:
            msg = """
Cannot find allprojects in project build.gradle.

Please add allprojects and run setup again.
"""
            raise code_snippet.SnippetExecutionError(msg)

        repo_start, _ = file_manager.find_block_indexes(
            lines[start : end + 1], "repositories"
        )
        if repo_start is None:
            msg = """
Cannot find repositories in project build.gradle.

Please add a repositories section in allproject.
"""
            raise code_snippet.SnippetExecutionError(msg)

        code = """        maven {
            url 'https://raw.github.com/fritzlabs/fritz-repository/master'
        }
"""
        lines.insert(start + repo_start + 1, code)
        self.path.write_text("".join(lines))
