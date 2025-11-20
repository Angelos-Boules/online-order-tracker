import { signOut } from "../auth";

function Navbar() {
    return (
        <nav className="navbar navbar-dark bg-dark px-3 mb-4 shadow-sm">
        <span className="navbar-brand mb-0 h1">Buy-N-Track</span>

        <button className="btn btn-outline-light" onClick={signOut}>
            Sign Out
        </button>
        </nav>
    );
}

export default Navbar;