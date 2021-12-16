import React from 'react'
import loadable from '@loadable/component'
import { hot } from 'react-hot-loader'
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom'

import './App.scss'

import NavBar from './components/NavBar.jsx'
import ExamRouter from './components/ExamRouter.jsx'
import Footer from './components/Footer.jsx'
import Loading from './views/Loading.jsx'

const Home = loadable(() => import('./views/Home.jsx'), { fallback: <Loading /> })
const AddExam = loadable(() => import('./views/AddExam.jsx'), { fallback: <Loading /> })
const Graders = loadable(() => import('./views/Graders.jsx'), { fallback: <Loading /> })
const Fail = loadable(() => import('./views/Fail.jsx'), { fallback: <Loading /> })

const PrivateRoute = ({ isAuthenticated, render, ...rest }) => {
  return (
    <Route
      {...rest}
      render={({ location, history, match }) =>
        isAuthenticated
          ? (
              render({ location, history, match })
            )
          : (
          <Redirect
            to={{
              pathname: '/',
              state: { from: location }
            }}
          />
            )}
    />
  )
}

class App extends React.Component {
  menu = React.createRef();

  state = {
    examID: null,
    /*
    * The id of the current user. An undefined user means that the App has not check the backend for the registrered
    * user yet, hence wait for the response before going to the desired url by showing a Home/Welcome screen.
    * Instead, a null user means that is not logged in, then go to the Home page through the router.
    */
    graderID: undefined
  }

  selectExam = (id) => this.setState({ examID: parseInt(id) })

  updateExamList = () => {
    if (this.menu.current) {
      this.menu.current.updateExamList()
    }
  }

  setGrader = (grader) => this.setState({ graderID: grader ? grader.id : null })

  render () {
    const updateExamList = this.menu.current ? this.menu.current.updateExamList : () => {}
    const updateGraderList = this.menu.current ? this.menu.current.updateGraderList : () => {}
    const setHelpPage = this.menu.current ? this.menu.current.setHelpPage : (help) => {}
    const isAuthenticated = this.state.graderID !== null

    return (
      <Router>
        <div>
          <NavBar examID={this.state.examID} setGrader={this.setGrader} ref={this.menu} />
          {this.state.graderID === undefined
            ? <Home />
            : <Switch>
              <Route exact path='/' component={Home} />
              <PrivateRoute
                isAuthenticated={isAuthenticated}
                exact path='/exams'
                render={({ history }) => <AddExam updateExamList={updateExamList} changeURL={history.push} />}
              />
              <PrivateRoute
                isAuthenticated={isAuthenticated} path='/exams/:examID/' render={({ match }) =>
                  <ExamRouter
                    parentMatch={match}
                    graderID={this.state.graderID}
                    selectExam={this.selectExam}
                    updateExamList={updateExamList}
                    setHelpPage={setHelpPage}
                  />}
              />
              <PrivateRoute
                isAuthenticated={isAuthenticated} exact path='/graders' render={() =>
                  <Graders updateGraderList={updateGraderList} />}
              />
              <Route
                exact path='/unauthorized' render={() =>
                  <Fail message='Your account is not authorized to access this instance of Zesje.' />}
              />
              <Route render={() =>
                <Fail message="404. Could not find that page :'(" />}
              />
            </Switch>}
          <Footer />
        </div>
      </Router>
    )
  }
}

export default hot(module)(App)
