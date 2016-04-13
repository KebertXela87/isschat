var ISSChatApp = angular.module('ISSChatApp', []);

function login(showhide){
    if(showhide == "show"){
        document.getElementById('popupbox').style.visibility="visible";
        document.getElementById('loggedin').style.visibility="hidden";
        document.getElementById('loggedin2').style.visibility="hidden";
        document.getElementById('popupbox').style.height="170px";
    }
    else if(showhide == "hide"){
        document.getElementById('popupbox').style.visibility="hidden";
        document.getElementById('loggedin').style.visibility="visible";
        document.getElementById('loggedin2').style.visibility="visible";
        document.getElementById('popupbox').style.height="0px";
    }
}

function badpass(showhide){
    if(showhide == 'show'){
        document.getElementById('badpass').style.visibility="visible";
        document.getElementById('badpass').style.height="10px";
    }
    else if(showhide == 'hide'){
        document.getElementById('badpass').style.visibility="hidden";
        document.getElementById('badpass').style.height="0px";
    }
}

function showResults(showhide){
    if(showhide == 'show'){
        document.getElementById('searchpane').style.visibility="visible";
        document.getElementById('noresults').style.visibility="hidden";
        document.getElementById('noresults').style.height="10px";
    }
    else if(showhide == 'hide'){
        document.getElementById('searchpane').style.visibility="hidden";
        document.getElementById('noresults').style.visibility="visible";
        document.getElementById('noresults').style.height="0px";
    }
}

ISSChatApp.controller('ChatController', function($scope){
    var socket = io.connect('https://' + document.domain + ':' + location.port + '/iss');
    
    $scope.messages = [];
    $scope.name = '';
    $scope.text = '';
    $scope.roomName = '';
    $scope.rooms = [];
    $scope.searchTerm = '';
    $scope.searchResults = [];
    $scope.currentRoom = '';
    
    $scope.joinRoom = function(room) {
        console.log('Attempting to join room: ', room);
        socket.emit('on_join', room);
    };
    
    socket.on('joined', function(jRoom) {
        console.log('room: ', jRoom);
        $scope.currentRoom = jRoom;
        $scope.$apply();
    });
    
    socket.on('joinedGeneral', function() {
        $scope.currentRoom = 'General'; 
    });
    
    $scope.createRoom = function createRoom() {
        console.log('Creating room: ', $scope.roomName);
        socket.emit('createRoom', $scope.roomName);
        $scope.roomName = '';
    };
    
    socket.on('createRoom', function(room) {
        console.log('Im creating the room: ' + room);
        $scope.rooms.push(room);
        $scope.$apply();
    });
    
    socket.on('message', function(msg) {
        console.log(msg);
        $scope.messages.push(msg);
        $scope.$apply();
        var elem = document.getElementById('msgpane');
        elem.scrollTop = elem.scrollHeight;
    });
    
    $scope.send = function send() {
        console.log('Sending message: ', $scope.text);
        socket.emit('message', $scope.text);
        $scope.text = '';
    };
    
    socket.on('refreshMessages', function() {
        $scope.messages.pop();
    });
    
    socket.on('searchResult', function(ser) {
        console.log(ser);
        $scope.searchResults.push(ser);
        $scope.$apply();
    });
    
    socket.on('showResults', function() {
       console.log("Results found");
       showResults('show');
    });
    
    socket.on('showNoResults', function() {
       console.log("Results not found");
       showResults('hide');
    });
    
    $scope.search = function search() {
        console.log('Searching for: ', $scope.searchTerm);
        $scope.searchResults = [];
        socket.emit('search', $scope.searchTerm);
        $scope.searchTerm = '';
    };
    
    $scope.setName = function setName() {
        console.log($scope.name);
        socket.emit('identify', $scope.name);
        $scope.$apply();
    };
    
    socket.on('connect', function(){
        console.log('connected');
        $scope.setName();
    });
    
    $scope.processLogin = function processLogin() {
        console.log("Trying to log in");
        //login('hide');
        socket.emit('login', $scope.password)
    }
    
    socket.on('goodlogin', function() {
       console.log("Logged In");
       login('hide');
       badpass('hide');
    });
    
    socket.on('badlogin', function() {
       console.log("NOT Logged In");
       login('show');
       badpass('show');
    });
    
});