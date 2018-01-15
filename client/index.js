/*
    ./client/index.js
    which is the webpack entry file
*/
// @flow
import 'bulma/css/bulma.css';
import 'font-awesome/css/font-awesome.css';
import React from 'react';
import ReactDOM from 'react-dom';
import Loadable from 'react-loadable';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';


const Loading = () => <div>Loading...</div>;

const Home = Loadable({
  loader: () => import('./views/Home'),
  loading: Loading,
});
const Grade = Loadable({
  loader: () => import('./views/Grade'),
  loading: Loading,
});
const Upload = Loadable({
  loader: () => import('./views/Upload'),
  loading: Loading,
});
const AddStudents = Loadable({
  loader: () => import('./views/AddStudents'),
  loading: Loading,
});
const CheckStudents = Loadable({
  loader: () => import('./views/CheckStudents'),
  loading: Loading,
});
const AddGraders = Loadable({
  loader: () => import('./views/AddGraders'),
  loading: Loading,
});
const Reset = Loadable({
  loader: () => import('./views/Reset'),
  loading: Loading,
});


ReactDOM.render((
  <Router>
    <Switch>
     	<Route exact path="/" component={Home} />
      <Route path="/grade" component={Grade} />
     	<Route path="/upload" component={Upload} />
      <Route path="/addstudents" component={AddStudents} />
      <Route path="/checkstudents" component={CheckStudents} />
      <Route path="/addgraders" component={AddGraders} />
      <Route path="/reset" component={Reset} />
    </Switch>
  </Router>
), document.getElementById('root'));
