## What is it?

Silly Server can help you to mock some HTTP services which are not implemented yet, but you are really want to use them NOW.

It can mock GET, POST, PUT, DELETE and some more rarely used HTTP methods. 

## How?

Mocking service is as simple as creating directory and few files within it just like that:

    somedir/
        GET            # response content for GET /
        GET_H          # status and headers for GET /
        other_dir/
            GET        # response content for GET /other_dir
            POST       # response content for POST /other_dir
            POST_H     # status and headers for POST /other_dir

And then running silly server:

    ./ss.py -d /path/to/somedir

Ready! It will be listening on port 8000 *(can be changed with -p option)* and wait for your HTTP requests.
You can do:
    
    $ curl localhost:8000
    % whatever you put into somedir/GET file %

    $ curl -d "postparam=value&pararam=25" -X POST "localhost:8000/other_dir?someparam=value"
    % somedir/other_dir/POST content%    

Meanwhile in terminal where you launched ss.py some logs will appear:

    localhost - - [19/Oct/2012 13:23:03] "POST /other_dir?someparam=value HTTP/1.1" 200 -

    Got some GET params here:
    someparam: ['value']

    Got some payload:
    postparam: ['value']
    pararam: ['25']

You can specify response status and headers within GET\_H, POST\_H, %yourmethod%\_H files. Format is simple:

    403
    content-type: text/html
    cool-header: i'm cool

So, first line is status code, other lines are headers.

## Check example!

Some example included:

    % ./ss.py -d example

    # go to other terminal

    % curl -X GET -v localhost:8000                                                          
    < HTTP/1.0 400 Bad Request
    < cool-header: OLOLO
    < 
    Your request was very bad.


    % curl -X GET -v localhost:8000/user/
    < HTTP/1.0 200 OK
    < whats-here: users list
    < 
    {
      "users": ["john", "anonymous"]
    }


    % curl -X GET -v localhost:8000/user/john/status 
    < HTTP/1.0 200 OK
    < 
    {
      "status": "drunk"
    }


    % curl -X GET -v localhost:8000/user/anonymous/status
    < HTTP/1.0 403 Forbidden
    < 
    You can't get status of anonymous, he is anonymous. lol.


    % curl -X POST -d "param=value&other_param=25" localhost:8000/user
    < HTTP/1.0 200 OK
    < content-type: maybe some json is here
    < 
    {
        "whatsup": "You just posted something."
    }


Have fun!