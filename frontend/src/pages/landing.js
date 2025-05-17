import '../styles/landing.css'
import { Link } from 'react-router-dom';

function Landing(){
    return(
        <div>
            <img className="landing-image" src="/images/landing/image.png" alt="Emerald Altar Background" />
            <img className="title-text" src="/images/landing/title-text.png" alt="Emerald Altar Title" />
            <Link to="/login" className="nav-button">ENTER</Link>
        </div>
    )
}

export default Landing