import 'bulma/css/bulma.css';
import 'font-awesome/css/font-awesome.css';
import React from 'react';
import ReactDOM from 'react-dom';
import Loadable from 'react-loadable';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';

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

    state = {
        examIndex: null,
        examList: []
    }

    componentDidMount() {
        this.updateExamList();
    }

    updateExamList = (callback, onlyList) => {
        api.get('exams')
            .then(exams => {
                if (exams.length) {
                    if (onlyList) {
                        this.setState({
                            examList: exams
                        })
                    } else {
                        this.setState({
                            examIndex: exams.length - 1,
                            examList: exams
                        }, callback)
                    }
                }
            })
            .catch(resp => {
                alert('failed to get exams (see javascript console for details)')
                console.error('failed to get exams:', resp)
            })
    }

    changeExam = (examID) => {
        const index = this.state.examList.findIndex(exam => exam.id === examID)
        if (index === -1) {
            alert('Wrong exam url entered');
            return;
        } else {
            this.setState({
                examIndex: index
            })
        }
    }

    render() {

        const exam = this.state.examIndex === null ? null : this.state.examList[this.state.examIndex];

        return (
            <Router>
                <div>
                    <NavBar exam={exam} list={this.state.examList} changeExam={this.changeExam} />
                    <Switch>
                        <Route exact path="/" component={Home} />
                        <Route path="/exams/:examID" render={({match}) => 
                            <Exam exam={exam} urlID={match.params.examID} changeExam={this.changeExam} updateList={this.updateExamList}/> }/>
                        <Route path="/exams" render={({history}) => 
                            <AddExam updateExamList={this.updateExamList} changeURL={history.push} /> }/>
                        <Route path="/students" render={() => 
                            <Students exam={exam} /> }/>
                        <Route path="/grade" render={() => (
                            exam && exam.submissions ? <Grade /> : <Fail message="No exams uploaded. Please do not bookmark URLs" />
                        )} />
                        <Route path="/statistics" render={() => (
                            exam && exam.submissions ? <Statistics /> : <Fail message="No exams uploaded. Please do not bookmark URLs" />
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
