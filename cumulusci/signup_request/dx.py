from simple_salesforce import Salesforce
from cumulusci.tasks.salesforce import BaseSalesforceApiTask
from cumulusci.oauth.salesforce import SalesforceOAuth2
from cumulusci.core.config import OrgConfig
import pprint

class BaseSignupRequestTask(BaseSalesforceApiTask):
    completed_statuses = ['Error','Success']

    #def _init_task(self):
        #super(BaseSignupRequestTask, self)._init_task()

    def _init_options(self, kwargs):
        super(BaseSignupRequestTask, self)._init_options(kwargs)
        self.signup = {}
        self.signup['FirstName'] = self.project_config.developer__first_name
        self.signup['LastName'] = self.project_config.developer__last_name
        self.signup['SignupEmail'] = self.project_config.developer__email
        self.signup['Country'] = self.project_config.developer__country
        self.signup['PreferredLanguage'] = self.project_config.developer__preferred_language
        self.signup['ShouldConnectToEnvHub'] = self.project_config.project__signup__should_connect_to_hub
        self.signup['IsSignupEmailSuppressed'] = self.project_config.project__signup__suppress_emails


# for now, gonna hard code a lot of the assumptions
# about what the org request is. once we get it working
# we can refactor.
class CreateRequest(BaseSignupRequestTask):
    task_options = {
        'name': {
            # the name will then create the: company, domain, username
            'description': "The name of the environment to create.",
            'required': True,
        },
        'edition': {
            'description': "The edition template to create from.",
            'required': True,
        },
        'signup_source' : {
            'description': "The SignupSource to pass in the SignupRequest"
        }
    }

    def _init_options(self, kwargs):
        super(CreateRequest, self)._init_options(kwargs)

        if not 'signup_source' in self.options:
            self.options['signup_source'] = self.project_config.developer__signup_source

        self.signup['Edition'] = self.options['edition']
        self.signup['SignupSource'] = self.options['signup_source']

        self.signup['Company'] = "{project} - {org}".format(
            project=self.project_config.project__name,
            org = self.options['name']
        )

        self.signup['Subdomain'] = self.project_config.project__signup__domain_prefix + self.options['name']
        self.signup['Username'] = "{email}.{domain_prefix}.{org}".format(
            email = self.project_config.developer__email,
            domain_prefix = self.project_config.project__signup__domain_prefix,
            org = self.options['name']
        )

        self.signup['ConnectedAppConsumerKey'] = self.project_config.keychain.get_connected_app().config['client_id']
        self.signup['ConnectedAppCallbackUrl'] = self.project_config.keychain.get_connected_app().config['callback_url']

    def _run_task(self):
        response = self.sf.SignupRequest.create(self.signup)
        result = self.sf.SignupRequest.get(response['id'])
        pprint.pprint(result)
        # probably should stash that id somewhere, but for now we'll build a second task that lets us check in on that signup

class RegisterRequest(BaseSignupRequestTask):
    task_options = {
        'id' : {'description': 'The SignupRequest record Id','required':True},
        'name' : {'description': 'The name to save the org as','required':True}
    }

    def _run_task(self):
        result = self.sf.SignupRequest.get(self.options['id'])

        sf_oauth = SalesforceOAuth2(
            self.project_config.keychain.get_connected_app().config['client_id'],
            self.project_config.keychain.get_connected_app().config['client_secret'],
            self.project_config.keychain.get_connected_app().config['callback_url'],
            False
        )
        token = sf_oauth.get_token(result['AuthCode'])
        org_config = OrgConfig(token)
        self.project_config.keychain.set_org(self.options['name'], org_config)
        pprint.pprint(result)
