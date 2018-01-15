import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';
import ReactTable from 'react-table'

class AddStudents extends React.Component {

    constructor(props) {
        super(props)
        var that = this ;

        that.state = {
            students: [],
            columns: [{
                    Header: 'Student #',
                    accessor: 'id'
                }, {
                    id: 'studentName',
                    Header: 'Name',
                    accessor: s => s.first_name + ' ' + s.last_name,
                }, {
                    Header: 'email',
                    accessor: 'email'
            }]
        }

        fetch('/api/students')
        .then((response) => response.json())
        .then((students) =>{
            that.setState({students: students})
        })
    }

    render() {


        return (
            <div>
                <NavBar />

                <Hero title='Add Students' subtitle='Tell me who made this exam' />

                <ReactTable columns={this.state.columns} data={this.state.students}/>

                <h1>React Router demo</h1>

                <Footer />
            </div>
        )
    }
}

export default AddStudents;
