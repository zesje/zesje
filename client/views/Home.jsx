import React from 'react'

import homeMarkdown from './home/home.md'

const Home = () => <div className='container content' dangerouslySetInnerHTML={{ __html: homeMarkdown }} />

export default Home
