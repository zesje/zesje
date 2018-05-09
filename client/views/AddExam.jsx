import React from 'react';
import Dropzone from 'react-dropzone'

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';

import * as api from '../api.jsx'

class Exams extends React.Component {

    onDropYAML = (accepted, rejected) => {
        if (rejected.length > 0) {
            alert('Please upload a YAML..')
            return
        }
        const data = new FormData()
        data.append('yaml', accepted[0])
        api.post('exams', data)
            .then(exam => {
                this.props.updateExamList()
                this.props.changeURL('/exams/' + exam.id);
            })
            .catch(resp => {
                alert('failed to upload yaml (see javascript console for details)')
                console.error('failed to upload YAML:', resp)
            })
    }


    render() {

        return (
            <div>

                <Hero title='Add exam' subtitle="first step" />

                <section className="section">

                    <div className="container">

                        <h3 className='title'>Upload new exam configuration YAML</h3>
                        <h5 className='subtitle'>Each exam should have a unique name.</h5>

                        <Dropzone accept=".yml, text/yaml, text/x-yaml, application/yaml, application/x-yaml"
                            style={{}} activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                            onDrop={this.onDropYAML}
                            disablePreview
                            multiple={false}
                        >
                            <DropzoneContent />
                        </Dropzone>

                    </div>

                </section>

            </div >
        )
    }
}

export default Exams;
