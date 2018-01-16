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
const Exams = Loadable({
  loader: () => import('./views/Exams'),
  loading: Loading,
});
const Students = Loadable({
  loader: () => import('./views/Students'),
  loading: Loading,
});
const Grade = Loadable({
  loader: () => import('./views/Grade'),
  loading: Loading,
});
const Graders = Loadable({
  loader: () => import('./views/Graders'),
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
      <Route path="/exams" component={Exams} />
      <Route path="/students" component={Students} />
      <Route path="/grade" component={Grade} />
      <Route path="/graders" component={Graders} />
      <Route path="/reset" component={Reset} />
    </Switch>
  </Router>
), document.getElementById('root'));
