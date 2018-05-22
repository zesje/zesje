import React from 'react';
import Dropzone from 'react-dropzone';

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';
import PDFEditor from '../components/PDFEditor.jsx';
import { Link } from 'react-router-dom'

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

    renderContent = (action) => {
        switch (action) {
            case 'preview':
                return <div>preview</div>
            case 'export':
                return <div>export</div>
            case 'edit':
                return <PDFEditor exam={this.props.exam} examID={this.state.examID} />
            default:
                return <div>Unsupported action</div>
        }
    }

    renderTabs = () => {
        const tabs = [
            {
                name: 'Edit',
                action: 'edit',
                icon: 'fa-edit',
            },
            {
                name: 'Preview',
                action: 'preview',
                icon: 'fa-eye',
            },
            {
                name: 'Export',
                action: 'export',
                icon: 'fa-download',
            },
        ]
        return (
            <div className='tabs is-centered'>
                <ul>
                    {tabs.map(tab =>
                        <li key={tab.action} className={this.props.action === tab.action ? 'is-active' : ''}>
                            <Link to={'/exams/' + this.props.urlID + '/' + tab.action} >
                                <span className='icon is-small'><i className={'fa ' + tab.icon} aria-hidden='true'></i></span>
                                <span>{tab.name}</span>
                            </Link>
                        </li>
                    )}
                </ul>
            </div>
        )
    }

    render() {
        const renderContent = this.renderContent(this.props.action)
        return <div>
            <Hero title='Exam details' subtitle={'Selected: ' + this.props.exam.name} />
            <section className='section'>
                {this.renderTabs()}
                <div className='container'>
                    {renderContent}
                </div>
            </section>
        </div>
    }
}

export default Exams;
