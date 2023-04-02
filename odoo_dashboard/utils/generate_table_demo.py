# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

import random

NOUN = ['People', 'History', 'Way', 'Art', 'World', 'Information', 'Map', 'Family', 'Food', 'Understanding', 'Theory',
        'Law', 'Bird', 'Literature', 'Problem', 'Software', 'Control', 'Knowledge', 'Power', 'Ability', 'Economics',
        'Love', 'Internet', 'Television', 'Science', 'Library', 'Nature', 'Fact', 'Product', 'Idea', 'Temperature',
        'Investment', 'Area', 'Society', 'Activity', 'Story', 'Industry', 'Media', 'Thing', 'Oven', 'Community',
        'Definition', 'Safety', 'Quality', 'Development', 'Language', 'Management', 'Player', 'Variety', 'Video',
        'Week', 'Security', 'Country', 'Exam', 'Movie', 'Organization', 'Equipment', 'Physics', 'News', 'Audience',
        'Fishing', 'Growth', 'Income', 'Marriage', 'User', 'Combination', 'Failure', 'Meaning', 'Medicine',
        'Philosophy', 'Teacher', 'Communication', 'Night', 'Chemistry', 'Disease', 'Disk', 'Energy', 'Nation', 'Road',
        'Role', 'Soup', 'Advertising', 'Location', 'Success', 'Addition', 'Apartment', 'Education', 'Math', 'Moment',
        'Painting', 'Politics', 'Attention', 'Decision', 'Event', 'Property', 'Shopping', 'Student', 'Wood',
        'Competition']

LENGTH = 12

def get_demo_data_for_custom_list_item(self, ttype):
    content = []
    currency = self.env.company.currency_id.name
    for _ in range(LENGTH):
        row = dict()
        row['id'] = -1
        row['data'] = dict()
        row['widget'] = dict()
        row['pinned'] = False
        for key in ttype.keys():
            if ttype[key][0] == 'number' or ttype[key][1] == 'cell_percent' or ttype[key][1] == 'cell_monetary':
                row['data'][key] = random.random() * 1000
            elif ttype[key][0] == 'standard':
                row['data'][key] = random.choice(NOUN)
            elif ttype[key][1] == 'cell_monetary':
                row['widget'][key] = {ttype[key][2]: currency}
        content.append(row)
    return {
        'content': content,
        'options': {
            'maximum': LENGTH,
            'isDemo': True
        }
    }