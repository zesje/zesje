import React from 'react';
import Dropzone from 'react-dropzone';

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';

import * as api from '../api.jsx'

const ScanStatus = (props) => {
    let iconClass = 'fa fa-'
    switch (props.scan.status) {
        case 'processing':
            iconClass += 'refresh fa-spin'
            break
        case 'success':
            iconClass += 'check'
            break
        case 'error':
            iconClass += 'times'
            break
    }
    return (
        <div>
            {props.scan.name}&emsp;<i className={iconClass} />
            <i>&nbsp;{props.scan.message}</i>
        </div>
    )
}

class Submissions extends React.Component {

    state = {
        scans: [],
        submissions: [],
        examID: null,
    };

    updateScans = () => {
        api.get('scans/' + this.props.exam.id)
            .then(scans => {
                if (JSON.stringify(scans) != JSON.stringify(this.state.scans)) {
                    this.setState({
                        scans: scans
                    })
                    this.props.updateSubmission()
                    this.updateSubmissions()
                }
            })
    }

    updateSubmissions = () => {
        api.get('submissions/' + this.props.exam.id)
            .then(submissions => {
                console.log(submissions)
                this.setState({
                    submissions: submissions.map(sub => ({
                        id: sub['id'],
                        missing: sub['missing_pages']
                    }))
                })
            })
    }

    onDropPDF = (accepted, rejected) => {
        if (rejected.length > 0) {
            alert('Please upload a scan PDF.')
            return
        }
        accepted.map(file => {
            const data = new FormData()
            data.append('pdf', file)
            api.post('scans/' + this.props.exam.id, data)
                .then(() => {
                    this.updateScans();
                })
                .catch(resp => {
                    alert('failed to upload pdf (see javascript console for details)')
                    console.error('failed to upload PDF:', resp)
                })
        })
    }

    componentDidMount = () => {
        this.scanUpdater = setInterval(this.updateScans, 1000)
        // TODO: remove this when https://gitlab.kwant-project.org/zesje/zesje/issues/173
        //       has been solved. This is a
        api.get('students')
            .then(students => {
                if (students.length == 0) {
                    alert("You have not yet uploaded any students. " +
                        "If you don't upload students before the scans " +
                        "then we can't automatically assign students " +
                        "to their submissions")
                }
            })
    }

    componentWillUnmount = () => {
        clearInterval(this.scanUpdater);
    }

    render() {
        const missing_submissions = this.state.submissions.filter(s => s.missing.length > 0)

        const missing_submissions_status = (
            missing_submissions.length > 0 ?
                <div>
                    <p className="menu-label">
                        Missing Pages
                </p>
                    <ul className="menu-list">
                        {missing_submissions.map(sub =>
                            <li key={sub.id}>
                                Copy {sub.id} is missing pages {sub.missing.join(',')}
                            </li>
                        )}
                    </ul>
                </div>
                :
                null
        )

        return <div>

            <Hero title="Exam details" subtitle={"Selected: " + this.props.exam.name} />

            <section className="section">

                <div className="container">
                    <div className="columns">
                        <div className="column has-text-centered">
                            <h3 className='title'>Upload scans</h3>
                            <h5 className='subtitle'>Scanned pdf files</h5>
                            <Dropzone accept={"application/pdf"} style={{}}
                                activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                                onDrop={this.onDropPDF}
                                disablePreview
                                multiple
                            >
                                <DropzoneContent />
                            </Dropzone>
                            <br />
                            <aside className='menu'>
                                <p className="menu-label">
                                    Uploaded submissions: {this.state.submissions.length}
                                </p>

                                {missing_submissions_status}

                                <p className='menu-label'>
                                    Upload History
                                </p>
                                <ul className='menu-list'>
                                    {this.state.scans.map(scan =>
                                        <li key={scan.id}>
                                            <ScanStatus scan={scan} />
                                        </li>
                                    )}
                                </ul>
                            </aside>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    }
}

export default Submissions;
