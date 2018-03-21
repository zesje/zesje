import React from 'react';
import Dropzone from 'react-dropzone'

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';

import * as api from '../api.jsx'

const StatusPDF = (props) => {
    let iconClass = "fa fa-";
    switch (props.pdf.status) {
        case "processing":
            iconClass += "refresh fa-spin";
            break;
        case "success":
            iconClass += "check";
            break;
        case "error":
            iconClass += "times";
            break;
    }
    return (
        <div>
            {props.pdf.name}&emsp;<i className={iconClass} />
            <i>&nbsp;{props.pdf.message}</i>
        </div>
    )
}

class Exams extends React.Component {

    state = {
        yaml: "",
        pdfs: []
    };

    loadExam = (id) => {
        if (this.props.exam.id !== parseInt(id)) {
            console.log('Changing exam id to ' + id)            
            this.props.changeExam(parseInt(id));
        }

        api.get('exams/' + id)
            .then(exam => {
                this.setState({
                    yaml: exam.yaml
                })
            })
    }

    putYaml = () => {
        api.patch('exams/' + this.props.urlID, { yaml: this.state.yaml })
            .then(() => alert('thank you for the update; it was delicious'))
            .catch(resp => {
                alert('failed to update the YAML (see javascript console)')
                console.error('failed to update YAML', resp)
            })
    }

    updateYaml = (event) => {
        this.setState({
            yaml: event.target.value
        })
    }

    updatePDFs = () => {
        api.get('pdfs/' + this.props.urlID)
            .then(pdfs =>
                this.setState({
                        pdfs: pdfs
                })
            )
    }

    onDropPDF = (accepted, rejected) => {
        if (rejected.length > 0) {
            alert('Please upload a PDF..')
            return
        }
        accepted.map(file => {
            const data = new FormData()
            data.append('pdf', file)
            api.post('pdfs/' + this.props.urlID, data)
                .then(() => {
                    api.get('pdfs/' + this.props.urlID)
                        .then(pdfs =>
                            this.setState({
                                pdfs: pdfs
                            })
                        )
                })
                .catch(resp => {
                    alert('failed to upload pdf (see javascript console for details)')
                    console.error('failed to upload PDF:', resp)
                })
        })
    }

    componentDidMount = () => {
        this.loadExam(this.props.urlID);
        this.pdfUpdater = setInterval(this.updatePDFs, 1000)        
    }

    componentWillReceiveProps = (newProps) => {
        if (newProps.urlID !== this.props.urlID) {
            this.loadExam(newProps.urlID)    
        }
    }

    componentWillUnmount = () => {
        clearInterval(this.pdfUpdater);
    }

    render() {

        return <div>

            <Hero title="Exam details" subtitle={"Selected: " + this.props.exam.name} />

            <section className="section">

                <div className="container">
                    <div className="columns">


                        <div className="column has-text-centered">
                            <h3 className='title'>Tweak the config</h3>
                            <h5 className='subtitle'>to fix possible misalignments</h5>
                            <textarea className="textarea" rows="10"
                                value={this.state.yaml} onChange={this.updateYaml} />
                            <button className='button is-success'
                                onClick={this.putYaml}>
                                Save
                            </button>
                        </div>


                        <div className="column has-text-centered">
                            <h3 className='title'>And upload PDF's</h3>
                            <h5 className='subtitle'>we will work some magic!</h5>
                            <Dropzone accept={"application/pdf"} style={{}}
                                activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                                onDrop={this.onDropPDF}
                                disablePreview
                                multiple
                            >
                                <DropzoneContent/>
                            </Dropzone>

                            <br />
                            <aside className="menu">
                                <p className="menu-label">
                                    Previously uploaded
                                </p>
                                <ul className="menu-list">
                                    {this.state.pdfs.map(pdf =>
                                        <li key={pdf.id}><StatusPDF pdf={pdf} /></li>
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

export default Exams;
