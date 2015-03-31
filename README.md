# wunderlist-python
Example code on how to talk to the Wunderlist API from Python

All code is tested on [pythonanywhere.com](http://pythonanywhere.com/) with a default Flask deployment on a Hacker account.

Three working examples on how to talk to the [Wunderlist API](https://developer.wunderlist.com/):

* `wunderlist_flask_demo.py` is a simple demo of `GET`, `PUT` and `PATCH` with the Wunderlist API,

* `coursera_calendar_connector.py` makes Wunderlist tasks with due dates for all your currently active Coursera classes,

* `aggregate_foursquare_friends_tips.py` makes Wunderlist tasks from tips on places in your home city from your Foursqaure friends.

If you'd like to run these examples you have to configure the rescpective `SERVICE_NAME_oauth.json` files renaming the samples and setting the `callback url` - it should be `callback/SERVICE` - and the 'client_id' plus 'client_secret' obtained at the respective service providers, see the links in the Python files. 

The current flow of the pages is going like this as specified by the `redirect` fields:

```
/ -> non-WL authentication -> non-WL callback -> WL auth -> WL callback -> /logic
```


Thanks to [Torsten](https://github.com/torsten) for pointing in directions and [Franziska](https://github.com/vsmart) for the simple `urllib`-based approach on how to talk to the WL API.
