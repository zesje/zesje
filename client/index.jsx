import 'bulma/css/bulma.css';
import 'font-awesome/css/font-awesome.css';
import React from 'react';
import ReactDOM from 'react-dom';
import Loadable from 'react-loadable';
import {BrowserRouter as Router, Route, Switch, Redirect} from 'react-router-dom';

import * as api from './api.jsx'

import NavBar from './components/NavBar.jsx';
import Footer from './components/Footer.jsx';
import Loading from './views/Loading.jsx';

const Home = Loadable({
  loader: () => import('./views/Home.jsx'),
  loading: Loading
});
const AddExam = Loadable({
  loader: () => import('./views/AddExam.jsx'),
  loading: Loading
});
const Exam = Loadable({
    loader: () => import('./views/Exam.jsx'),
    loading: Loading
  });
const Students = Loadable({
  loader: () => import('./views/Students.jsx'),
  loading: Loading
});
const Grade = Loadable({
  loader: () => import('./views/Grade.jsx'),
  loading: Loading
});
const Graders = Loadable({
  loader: () => import('./views/Graders.jsx'),
  loading: Loading
});
const Statistics = Loadable({
  loader: () => import('./views/Statistics.jsx'),
  loading: Loading
});
const Reset = Loadable({
  loader: () => import('./views/Reset.jsx'),
  loading: Loading
});
const Fail = Loadable({
    loader: () => import('./views/Fail.jsx'),
    loading: Loading
})


class App extends React.Component {

    menu = React.createRef();

    state = {
        exam: {
            id: null,
            name: "",
            submissions: [],
            problems: [],
            yaml: ""
        }
    }

    updateExam = (examID) => {
        api.get('exams/' + examID)
            .then(ex => this.setState({
                    exam: ex
                }))
    }
    updateSubmission = (index, sub) => {
        if (index == undefined) {
            api.get('submissions/' + this.state.exam.id)
            .then(subs => this.setState({
                exam: {
                    ...this.state.exam,
                    submissions: subs
                }
            }))
        } else {
            if (sub) {
                if (JSON.stringify(sub) != JSON.stringify(this.state.exam.submissions[index])) {
                    let newList = this.state.exam.submissions;
                    newList[index] = sub;
                    this.setState({
                        exam: {
                            ...this.state.exam,
                            submissions: newList
                        }
                    })
                }
            } else {
                api.get('submissions/' + this.state.exam.id + '/' + this.state.exam.submissions[index].id)
                    .then(sub => {
                        if (JSON.stringify(sub) != JSON.stringify(this.state.exam.submissions[index])) {
                            let newList = this.state.exam.submissions;
                            newList[index] = sub;
                            this.setState({
                                exam: {
                                    ...this.state.exam,
                                    submissions: newList
                                }
                            })
                        }
                    })
            }
        }
    }

    render() {

        const exam = this.state.exam

        return (
            <Router>
                <div>
                    <NavBar exam={exam} updateExam={this.updateExam} ref={this.menu} />
                    <Switch>
                        <Route exact path="/" component={Home} />
                        <Route path="/exams/:examID/:action?" render={({match}) =>
                            <Exam
                                exam={exam}
                                urlID={match.params.examID}
                                action={match.params.action || 'edit' }
                                updateExam={this.updateExam}
                                updateSubmission={this.updateSubmission}/> }/>
                        <Route path="/exams" render={({history}) =>
                            <AddExam updateExamList={() => this.menu.current.updateExamList()} changeURL={history.push} /> }/>
                        <Route path="/students" render={() =>
                            <Students exam={exam} updateSubmission={this.updateSubmission}/> }/>
                        <Route path="/grade" render={() => (
                            exam.submissions.length ? <Grade exam={exam} updateSubmission={this.updateSubmission}/> : <Fail message="No exams uploaded. Please do not bookmark URLs" />
                        )} />
                        <Route path="/statistics" render={() => (
                            exam.submissions.length ? <Statistics exam={exam} /> : <Fail message="No exams uploaded. Please do not bookmark URLs" />
                        )} />
                        <Route path="/graders" component={Graders} />
                        <Route path="/reset" component={Reset} />
                        <Route render={() =>
                            <Fail message="404. Could not find that page :'(" /> }/>
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
