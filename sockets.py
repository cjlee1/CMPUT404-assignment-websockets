#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle, 2019 CALVIN lee
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, request,redirect
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True
# abram hindle
# client stuff which is necessary for subscribe ws and read ws and other stuff
# https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py

def send_all(msg):
    for client in clients:
        client.put( msg )

def send_all_json(obj):
    send_all( json.dumps(obj) )

class Client:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, v):
        self.queue.put_nowait(v)

    def get(self):
        return self.queue.get()

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

myWorld = World()       
clients = [] 

def set_listener( entity, data ):
    ''' do something with the update ! '''


myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    # title: Redirecting to url in flask
    # author: Xavier Combelle
    # date: 2019-03-02
    # url: https://stackoverflow.com/questions/14343812/redirecting-to-url-in-flask
    return redirect("/static/index.html",code=301)

def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    # abram hindle 
    #  implement a greenlit function 
# https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py 
    try:       
        while True:
            msg = ws.receive()
            print ("WS RECV: %s" % msg)
            if (msg is not None):
                packet = json.loads(msg)
                send_all_json( packet )
                # author : sberry
                # looking at multiple items in for loop for python
                # https://stackoverflow.com/questions/44026946/iterating-through-multiple-values-for-one-dict-key-in-python
                for world, info in packet.items():
                    myWorld.set(world,info)
            else:
                break
    except :
        pass
'''Done'''

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    # abram hindle
    # in subscribe_socket in abram hindles example
    # https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py
    client = Client()
    clients.append(client)
    g = gevent.spawn( read_ws, ws, client )    
    try:
        while True:
            # block here
            msg = client.get()
            ws.send(msg)
    except Exception as e:# WebSocketError as e:
        print ("WS Error %s" % e)
    finally:
        clients.remove(client)
        gevent.kill(g)

# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    return flask.Response(response=json.dumps(myWorld.set(entity,flask_post_json()).get(entity)))

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    if request.method == "GET":
        return flask.jsonify(myWorld.world()),200
    elif (request.method == "POST"): #POST method

        dict_data=flask_post_json()
        # under the assumption that post and get are different because post should post data while get just gets the data
        # this way will go into the json data, loop over the data , get the entity and have the updated worlds be put into the
        # current world and the send it
        for k in dict_data.items():
            entity=k[0]
            world =k[1]
            for k2 in world:
                # print(k2)
                # print("hi")
                # world=myWorld.world()
                # print(world)
                myWorld.update(entity,k2,world[k2])

                #codegeek
        # returning json to flask
        # https://stackoverflow.com/questions/13081532/return-json-response-from-flask-view
        return flask.jsonify(myWorld.world()),200

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    return flask.Response(response=json.dumps(myWorld.get(entity)),status=200)


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    myWorld.clear()
    return (flask.jsonify(myWorld.world()),200)



if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
