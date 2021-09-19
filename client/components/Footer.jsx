import React from 'react'

const Hero = (props) => {
  return (
    <footer className='footer'>
      <div className='container'>
        <div className='content has-text-centered'>
          <p>
            <strong>Zesje</strong> by
            <a
              href='https://gitlab.kwant-project.org/zesje/zesje/blob/master/AUTHORS.md'
              target='_blank'
              rel="noreferrer"
            > the team
            </a>.
            The code is licensed under
            <a href='https://choosealicense.com/licenses/agpl-3.0/' target='_blank' rel="noreferrer"> AGPLv3 </a>
            and available
            <a href='https://gitlab.kwant-project.org/zesje/zesje/' target='_blank' rel="noreferrer"> here</a>.
            <br />
            Version {__ZESJE_VERSION__}
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Hero
