import React from 'react';

function Sidebar() {
  return (
    <aside style={{ background: '#f4f4f4', padding: '1rem', width: '200px' }}>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        <li><a href="#item1">Menu Item 1</a></li>
        <li><a href="#item2">Menu Item 2</a></li>
        <li><a href="#item3">Menu Item 3</a></li>
      </ul>
    </aside>
  );
}

export default Sidebar;