import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import Noti from '../components/Noti.jsx'

class Grade extends React.Component {


    click = () => {
        this.Noti.new('Heeeej dit werkt');
    }

    render() {

        return (
            <div>

                <NavBar />

                <Hero title='Grade' subtitle='This is where the magic happens!' />

                <section className="section">

                    <div className="container">

                        <h1>React Router demo</h1>
                        Hoi dit de Grade

                        <Noti ref={(noti) => { this.Noti = noti; }} />

                        <button className="button" onClick={this.click}>Hii</button>

                    </div>

                </section>

                <Footer />

            </div>
        )
    }
}

export default Grade;