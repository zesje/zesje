import React from 'react';
import Fuse from 'fuse.js';

import * as api from '../../api';

import StudentPanelBlock from './StudentPanelBlock.jsx';

class SearchPanel extends React.Component {

    students = [
        {
            id: 0,
            firstName: "",
            lastName: "",
            email: ""
        }
    ];

    state= {
        input: '',
        selected: 0,
        result: []
    }

    componentDidMount = () => {
        api.get('students')
            .then(students => {
                this.students = students;
            })
            .catch(err => {
                alert('failed to get students (see javascript console for details)')
                console.error('failed to get students:', err)
                throw err
            })
    }

    search = (event) => {

        const options = {
            shouldSort: true,
            threshold: 0.6,
            location: 0,
            distance: 100,
            maxPatternLength: 32,
            minMatchCharLength: 1,
            keys: [
                "id",
                "firstName",
                "lastName"
            ]
        };
        const fuse = new Fuse(this.students, options);
        const result = fuse.search(event.target.value).slice(0, 10);

        this.setState({
            input: event.target.value,
            selected: 0,
            result: result
        })
    }

    specialKey = (event) => {
        if (event.keyCode === 38 || event.keyCode === 40) {
            event.preventDefault();
            let sel = this.state.selected;

            if (event.keyCode == 38 && sel > 0) sel--;
            if (event.keyCode == 40 && sel < this.state.result.length - 1) sel++;

            this.setState({
                ...this.state,
                selected: sel
            })
        }
        if (event.keyCode === 27) this.searchInput.blur();
        if (event.keyCode === 13) {
            const stud = this.state.result[this.state.selected];
            if (!stud) return;

            this.props.matchStudent(stud.id);
        }
    }

    selectStudent = (event) => {

        if (event.target.selected) {
            this.props.matchStudent(this.state.result[this.state.selected].id);
        } else {
            const index = this.state.result.findIndex(result => result.id == event.target.id);
            this.setState({
                ...this.state,
                selected: index
            })
        }
    }

    listMatchedStudent = () => {
        const studIndex = this.students.findIndex(stud =>
            stud.id === this.props.studentID);
        const stud = studIndex > -1 ? [this.students[studIndex]] : [];

        this.setState({
            input: '',
            selected: 0,
            result: stud
        })

        if (!this.props.validated) {
            this.searchInput.focus();
        }
    }

    render() {

        return (
            <div>
                <p className="panel-heading">
                    Students
                </p>
                <div className="panel-block">
                    <p className="control has-icons-left">
                        <input className="input" type="text"
                            ref={(input) => { this.searchInput = input; }}
                            value={this.state.input} onChange={this.search} onKeyDown={this.specialKey} />

                        <span className="icon is-left">
                            <i className="fa fa-search"></i>
                        </span>
                    </p>
                </div>
                {this.state.result.map((student, index) =>
                    <StudentPanelBlock key={student.id} student={student}
                        selected={index === this.state.selected}
                        matched={student.id === this.props.studentID && this.props.validated}
                        selectStudent={this.selectStudent} />
                )}
            </div>

        )
    }

}

export default SearchPanel;