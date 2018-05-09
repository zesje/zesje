import React from 'react';
import { Link } from 'react-router-dom';

import * as api from '../api.jsx'

const BurgerButton = (props) => (
    <button className={"button navbar-burger" + (props.foldOut ? " is-active" : "")}
        onClick={props.burgerClick}>
        <span></span>
        <span></span>
        <span></span>
    </button>
)

const ExamDropdown = (props) => (
    <div className="navbar-item has-dropdown is-hoverable">
        <Link className="navbar-link" to={'/exams/' + (props.exam.id ? props.exam.id : "")}>
            {props.exam.id ? <i>{props.exam.name}</i> : "Add exam"}
        </Link>
        <div className="navbar-dropdown">
            {props.list.map((exam) => (
                <Link className={"navbar-item" + (props.exam.id === exam.id ? " is-active" : "")}
                    to={'/exams/' + exam.id} key={exam.id} >
                    <i>{exam.name}</i>
                </Link>
            ))}
            <hr className="navbar-divider" />
            <Link className="navbar-item" to={'/exams'} >
                Add new
            </Link>
        </div>
    </div>
)

class NavBar extends React.Component {

    state = {
        foldOut: false,
        examList: []
    }

    componentDidMount = () => {
        this.updateExamList();
    }

    updateExamList = () => {
        api.get('exams')
            .then(exams => {
                this.setState({
                    examList: exams
                })
                if (this.props.exam.id == null && exams.length) this.props.updateExam(exams[exams.length - 1].id)
            })
    }

    burgerClick = () => {
        this.setState({
            foldOut: !this.state.foldOut
        })
    }

    render() {

        const examStyle = this.props.exam.submissions.length ? {} : { pointerEvents: 'none', opacity: .65 }

        return (
            <nav className="navbar" role="navigation" aria-label="dropdown navigation">

                <div className="navbar-brand">
                    <div className="navbar-item has-text-info">
                        <span className="icon is-medium">
                            <i className="fa fa-edit fa-2x"></i>
                        </span>
                    </div>

                    <Link className="navbar-item has-text-info" to='/'><b>Zesje</b></Link>
                    <div className="navbar-item"></div>

                    <BurgerButton foldOut={this.props.foldOut} burgerClick={this.burgerClick} />
                </div>

                <div className={"navbar-menu" + (this.state.foldOut ? " is-active" : "")} onClick={this.burgerClick}>
                    <div className="navbar-start">

                        {this.state.examList.length ?
                            <ExamDropdown exam={this.props.exam} list={this.state.examList} />
                            :
                            <Link className="navbar-item" to='/exams'>Add exam</Link>
                        }

                        <Link className="navbar-item" to='/students'>Students</Link>
                        <Link className="navbar-item" style={examStyle} to='/grade'><strong><i>Grade</i></strong></Link>
                        <Link className="navbar-item" style={examStyle} to='/statistics'>Statistics</Link>
                    </div>

                    <div className="navbar-end">
                        <Link className="navbar-item" to='/graders'>Manage graders</Link>
                        <Link className="navbar-item has-text-info" to='/reset'>reset</Link>
                        <div className="navbar-item">
                            <i>Version { __COMMIT_HASH__ }</i>
                        </div>
                    </div>
                </div>
            </nav>
        )
    }

}

export default NavBar;
