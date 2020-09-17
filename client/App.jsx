import React from 'react'
import Loadable from 'react-loadable'
import { hot } from 'react-hot-loader'
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom'

import 'bulma/css/bulma.css'
import 'react-bulma-notification/build/css/index.css'
import 'font-awesome/css/font-awesome.css'

import NavBar from './components/NavBar.jsx'
import ExamRouter from './components/ExamRouter.jsx'
import Footer from './components/Footer.jsx'
import Loading from './views/Loading.jsx'

const Home = Loadable({
  loader: () => import('./views/Home.jsx'),
  loading: Loading
})
const AddExam = Loadable({
  loader: () => import('./views/AddExam.jsx'),
  loading: Loading
})
const Graders = Loadable({
  loader: () => import('./views/Graders.jsx'),
  loading: Loading
})

const Login = Loadable({
  loader: () => import('./views/Login.jsx'),
  loading: Loading
})

const Fail = Loadable({
  loader: () => import('./views/Fail.jsx'),
  loading: Loading
})

const PrivateRoute = ({ isAuthenticated, render, ...rest }) => {
  return (
    <Route
      {...rest}
      render={({ location, history, match }) =>
        isAuthenticated ? (
          render({ location, history, match })
        ) : (
          <Redirect
            to={{
              pathname: '/login',
              state: { from: location }
            }}
          />
        )
      }
    />
  )
}

class App extends React.Component {
  menu = React.createRef();

  state = {
    examID: null,
    grader: null
  }

  selectExam = (id) => {
    this.setState({ examID: parseInt(id) })
  }

  updateExamList = () => {
    if (this.menu.current) {
      this.menu.current.updateExamList()
    }
  }

  changeGrader = (grader) => {
    this.setState({
      grader: grader
    })
    window.sessionStorage.setItem('graderID', grader ? grader.id : null)
  }

  render () {
    const grader = this.state.grader
    const updateExamList = this.menu.current ? this.menu.current.updateExamList : () => {}
    const updateGraderList = this.menu.current ? this.menu.current.updateGraderList : () => {}
    const setHelpPage = this.menu.current ? this.menu.current.setHelpPage : (help) => {}

    return (
      <Router>
        <div>
          <NavBar examID={this.state.examID} grader={grader} changeGrader={this.changeGrader} ref={this.menu} />
          <Switch>
            <Route exact path='/' component={Home} />
            <Route path='/login' render={({ history }) => <Login changeURL={history.push} />} />
            <PrivateRoute
              isAuthenticated={grader !== null}
              exact path='/exams'
              render={({ history }) => <AddExam updateExamList={updateExamList} changeURL={history.push} />}
            />
            <PrivateRoute isAuthenticated={grader !== null} path='/exams/:examID/' render={({ match }) =>
              <ExamRouter
                parentMatch={match}
                graderID={grader ? grader.id : null}
                selectExam={this.selectExam}
                updateExamList={updateExamList}
                setHelpPage={setHelpPage} />
            } />
            <Route exact path='/graders' render={() =>
              <Graders updateGraderList={updateGraderList} />} />
            <Route render={() =>
              <Fail message="404. Could not find that page :'(" />} />
          </Switch>
          <Footer />
        </div>
      </Router>
    )
  }
}

export default hot(module)(App)
