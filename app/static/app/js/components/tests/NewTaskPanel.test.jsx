import React from 'react';
import { shallow } from 'enzyme';
import NewTaskPanel from '../NewTaskPanel';

describe('<NewTaskPanel />', () => {
  it('renders without exploding', () => {
    const wrapper = shallow(<NewTaskPanel onSave={() => {}} onReview={() => {}}/>);
    expect(wrapper.exists()).toBe(true);
  })
});
