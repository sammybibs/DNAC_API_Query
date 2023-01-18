# Experimenting with DNAC, python and the API to front end the calls with Flask

See https://ramblings-one.com/Blogger/DNAC_API/ for development details from the ground up.

If anyone would like to contribute to this project, feel free to reach out to me **sammybibs@gmail.com** or check the above blog ^

## Version
1 : 18/Jan/2022 : First release of code published

# Change log:
* 0.1 : Initial beta release

# Running the app:
To load the app run 'python Web_app.py' in the /DNAC_Web_Server directory

# Filelog in /DNAC_Web_Server
* /cache/* : The locally cached files from sandboxdnac.cisco.com
* /StaticFiles/main.css : The stylesheet for the web pages
* /Templates/*.html : The HTML for the web pages
* /Templates/skelington.html : Base layout needed for future pages
* DNAC_API.py : API calls used to push/pull data from DNAC
* Dnac_data.yml : Lab and sandbox sever details **(the lab one can be changed with the GUI 'update DNAC' option)**
* requirements.txt : python requirements
* Web_app.py : **The flask app launch file, this file should be run to load this app**


## Upcoming changes required
1. Tidy up GUI menus (need nav menus in sub-pages)
2. Pre checks to see if server is alive (i.e the sandbox is often down)
3. Single password entry on load vs not on every page (then purge after inactivity of N)
4. Empty demo function with web-page/HTML to allow ease of adding to this
5. Fork the code to AWS and Webex bot
