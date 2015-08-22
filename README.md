# echo_kodi
**An Alexa Skills Kit app for finding out what shows are in your Kodi library by voice with the Amazon Echo**

Visit [this Maker Musings article](http://www.makermusings.com/2015/07/19/home-automation-with-amazon-echo-apps-part-1/) to learn more about using this code to integrate the Amazon Echo with your [Kodi](http://kodi.tv/) media center.

### Summary

If you want to go beyond simple on/off commands to integrate the Amazon Echo into your home automation, you may be able to use a "Skill", which is an app using the Alexa Skills Kit. echo_kodi is a Skill that gives you voice access to your Kodi media center, and allows you to ask the Echo about shows that are ready to watch. It includes the full web service needed for an Alexa Skill as well as a simple module that leverages the Kodi API.

### Instructions

You will need an Apache web server configured with mod_wsgi or equivalent functionality with another web server if you want to use these files unchanged. You will also need Python 2.7 and the [python-requests](http://docs.python-requests.org/en/latest/) library. 

Copy the files echo_handler.wsgi and kodi.py to a location where Apache can access them. Configure your web server to use echo_handler.wsgi for the virtual server or directory of your choosing, using WSGIScriptAlias or WSGIScriptAliasMatch. The Alexa Skills Kit will work only with https, so you must configure your server to use SSL. Restart Apache.

Edit kodi.py to have the IP address of your Kodi host.

Once you believe your web server is running properly, edit and use echo_test.sh to verify that your web sevrer returns a reasonable JSON response to Alexa requests.

Using a free Amazon developer's account, create your Skill in the developer console. 

On the Skill Information tab, fill out the details for your Skill including your web server's URL that you configured to use echo_handler.wsgi. 

On the Interaction Model tab, copy and paste the contents of alexa.intents to the Intent Schema. Copy and paste the contents of alexa.utternaces into the [utternace expander tool](http://www.makermusings.com/amazon-echo-utterance-expander/), and paste the expanded results into the Sample Utterances field.

Work through the SSL Certificate and Test tabs appropriately for your setup. Make sure you have a green checkmark on the Test tab.

Finally, test with your Echo by saying, "Alexa, ask <app name> what new shows we have".

