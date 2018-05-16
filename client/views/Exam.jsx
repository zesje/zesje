import React from 'react';
import Dropzone from 'react-dropzone';

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';
import PDFEditor from '../components/PDFEditor.jsx';

import * as api from '../api.jsx'

class Exams extends React.Component {

    state = {
        examID: null
    };

    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.exam.id != prevState.examID) {
            return {
                examID: newProps.exam.id
            }
        }
        return null
    }

    componentDidUpdate = (prevProps) => {
        if (prevProps.urlID !== this.props.urlID) {
            this.props.updateExam(this.props.urlID)
        }
    }

    componentDidMount = () => {
        if (this.props.urlID !== this.props.exam.id) this.props.updateExam(this.props.urlID)
    }

    render() {
        return <div>
            <Hero title="Exam details" subtitle={"Selected: " + this.props.exam.name} />
            <section className="section">
                <div className="container">
                    <PDFEditor examID={this.state.examID} />
                </div>
            </section>
        </div>
    }
}

export default Exams;
