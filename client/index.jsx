import 'bulma/css/bulma.css';
import 'font-awesome/css/font-awesome.css';
import React from 'react';
import ReactDOM from 'react-dom';
import Loadable from 'react-loadable';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';

import NavBar from './components/NavBar.jsx';
import Footer from './components/Footer.jsx';

const Loading = () => <div>Loading...</div>;

const Home = Loadable({
  loader: () => import('./views/Home.jsx'),
  loading: Loading,
});
const Exams = Loadable({
  loader: () => import('./views/Exams.jsx'),
  loading: Loading,
});
const Students = Loadable({
  loader: () => import('./views/Students.jsx'),
  loading: Loading,
});
const Grade = Loadable({
  loader: () => import('./views/Grade.jsx'),
  loading: Loading,
});
const Graders = Loadable({
  loader: () => import('./views/Graders.jsx'),
  loading: Loading,
});
const Statistics = Loadable({
  loader: () => import('./views/Statistics.jsx'),
  loading: Loading,
});
const Reset = Loadable({
  loader: () => import('./views/Reset.jsx'),
  loading: Loading,
});


class App extends React.Component {

    render() {

        return (
            <Router>
                <div>
                    <NavBar />
                    <Switch>
                        <Route exact path="/" component={Home} />
                        <Route path="/exams" component={Exams} />
                        <Route path="/students" component={Students} />
                        <Route path="/grade" component={Grade} />
                        <Route path="/graders" component={Graders} />
                        <Route path="/reset" component={Reset} />
                        <Route path="/statistics" component={Statistics} />
                    </Switch>
                    <Footer />
                </div>
            </Router>
        )
    }
}

var root = document.getElementById('root');
if (root == null) {
  throw new Error("no pad element");
} else {
  ReactDOM.render(<App />, root);
}
